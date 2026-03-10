# jarvis/backtest/engine.py
# Version: 1.0.0
# External deterministic backtest layer.
# External to jarvis/core/, jarvis/risk/, jarvis/portfolio/,
# jarvis/execution/, jarvis/orchestrator/ per FAS v6.1.0 architecture rules.
#
# DETERMINISM GUARANTEE:
#   No stochastic operations. No random number generation. No sampling.
#   No external state reads. No side effects. No file I/O. No logging.
#   No environment variable access. No global mutable state.
#   Output is a pure function of inputs.
#
# PURPOSE:
#   Rolls a sliding window over returns_series and asset_price_series,
#   delegating all risk and allocation logic to run_full_pipeline() at
#   each timestep. No risk or allocation logic is reimplemented here.
#
# DESIGN NOTE -- SYMBOL KEY:
#   run_full_pipeline() requires asset_prices: dict[str, float].
#   run_backtest() receives a scalar price series with no symbol names.
#   A fixed synthetic key "ASSET" is used to wrap each scalar price into
#   the required single-entry dict at every timestep. This is the only
#   valid deterministic approach that avoids reimplementing downstream
#   logic.
#
# EQUITY UPDATE CONTRACT:
#   equity[t] = equity[t-1] * (1.0 + returns_series[t] * position_size)
#   where position_size is the scalar extracted from the single-key
#   positions dict returned by run_full_pipeline().
#
# Standard import pattern:
#   from jarvis.backtest.engine import run_backtest

from jarvis.core.regime import GlobalRegimeState
from jarvis.orchestrator import run_full_pipeline

_SYNTHETIC_SYMBOL: str = "ASSET"
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


def run_backtest(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    args = [returns_series, window, initial_capital, asset_price_series, regime, meta_uncertainty]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_run_backtest__mutmut_orig, x_run_backtest__mutmut_mutants, args, kwargs, None)


def x_run_backtest__mutmut_orig(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_1(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window <= 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_2(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 21:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_3(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            None
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_4(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital < 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_5(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 1.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_6(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            None
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_7(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) == len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_8(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            None
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_9(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = None
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_10(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = None

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_11(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = None

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_12(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(None, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_13(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, None):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_14(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_15(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, ):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_16(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = None

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_17(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t + window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_18(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = None

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_19(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = None

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_20(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=None,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_21(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=None,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_22(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=None,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_23(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=None,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_24(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=None,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_25(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_26(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_27(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_28(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_29(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_30(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = None

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_31(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = None
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_32(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity / (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_33(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 - returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_34(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (2.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_35(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] / position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_36(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = None

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_37(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(None, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_38(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, None)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_39(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_40(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, )

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_41(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1.0000000001, updated_equity)

        equity_curve.append(equity)

    return equity_curve


def x_run_backtest__mutmut_42(
    returns_series: list[float],
    window: int,
    initial_capital: float,
    asset_price_series: list[float],
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> list[float]:
    """
    Deterministic rolling-window backtest over a single-asset return series.

    For each timestep t >= window:
      1. Slices returns_series[t - window : t] as the lookback window.
      2. Wraps asset_price_series[t] into a single-entry dict under the
         synthetic key "ASSET".
      3. Calls run_full_pipeline() to obtain position size.
      4. Extracts the scalar position size from the returned dict.
      5. Updates equity: equity * (1.0 + returns_series[t] * position_size).
      6. Appends updated equity to the equity curve.

    All risk assessment and allocation logic is delegated to
    run_full_pipeline(). Nothing is reimplemented here.

    Parameters
    ----------
    returns_series : list[float]
        Sequence of per-period returns. Must have length >= window.
        Passed as the lookback window to run_full_pipeline() at each step.
        No NaN or Inf values permitted (validated downstream by RiskEngine).
    window : int
        Lookback window size in periods. Must be >= 20 (RiskEngine minimum).
    initial_capital : float
        Starting equity value. Must be strictly positive.
        Passed as total_capital to run_full_pipeline() at each step.
    asset_price_series : list[float]
        Per-period asset prices. Must have the same length as returns_series.
        Each scalar price is wrapped into a single-entry dict at each step.
        All prices must be strictly positive (validated downstream).
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_full_pipeline() at every timestep.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
        Passed unchanged to run_full_pipeline() at every timestep.

    Returns
    -------
    list[float]
        Equity curve. One entry per timestep t where t >= window.
        Length is len(returns_series) - window.
        Returns an empty list if len(returns_series) == window
        (no full step available beyond the first window).

    Raises
    ------
    ValueError
        If window < 20.
        If initial_capital <= 0.
        If len(asset_price_series) != len(returns_series).
        Additional ValueError may propagate from run_full_pipeline()
        on invalid returns or price values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    regime and meta_uncertainty are held constant across all timesteps.
    This matches the function signature contract. Dynamic regime
    sequencing is out of scope for this module.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum). Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be strictly positive. Received: {initial_capital}"
        )

    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"asset_price_series and returns_series must have equal length. "
            f"Received: len(returns_series)={len(returns_series)}, "
            f"len(asset_price_series)={len(asset_price_series)}"
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop.
    # ------------------------------------------------------------------
    equity: float = initial_capital
    equity_curve: list[float] = []

    n: int = len(returns_series)

    for t in range(window, n):
        window_returns: list[float] = returns_series[t - window : t]

        asset_prices: dict[str, float] = {
            _SYNTHETIC_SYMBOL: asset_price_series[t]
        }

        positions: dict[str, float] = run_full_pipeline(
            returns_history=window_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices=asset_prices,
        )

        position_size: float = positions[_SYNTHETIC_SYMBOL]

        updated_equity: float = equity * (1.0 + returns_series[t] * position_size)
        # Capital floor: equity must never be negative or zero per FAS contract.
        # A minimum of 1e-10 preserves the strictly-positive invariant required
        # by run_full_pipeline() at the next timestep.
        equity = max(1e-10, updated_equity)

        equity_curve.append(None)

    return equity_curve

x_run_backtest__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_run_backtest__mutmut_1': x_run_backtest__mutmut_1, 
    'x_run_backtest__mutmut_2': x_run_backtest__mutmut_2, 
    'x_run_backtest__mutmut_3': x_run_backtest__mutmut_3, 
    'x_run_backtest__mutmut_4': x_run_backtest__mutmut_4, 
    'x_run_backtest__mutmut_5': x_run_backtest__mutmut_5, 
    'x_run_backtest__mutmut_6': x_run_backtest__mutmut_6, 
    'x_run_backtest__mutmut_7': x_run_backtest__mutmut_7, 
    'x_run_backtest__mutmut_8': x_run_backtest__mutmut_8, 
    'x_run_backtest__mutmut_9': x_run_backtest__mutmut_9, 
    'x_run_backtest__mutmut_10': x_run_backtest__mutmut_10, 
    'x_run_backtest__mutmut_11': x_run_backtest__mutmut_11, 
    'x_run_backtest__mutmut_12': x_run_backtest__mutmut_12, 
    'x_run_backtest__mutmut_13': x_run_backtest__mutmut_13, 
    'x_run_backtest__mutmut_14': x_run_backtest__mutmut_14, 
    'x_run_backtest__mutmut_15': x_run_backtest__mutmut_15, 
    'x_run_backtest__mutmut_16': x_run_backtest__mutmut_16, 
    'x_run_backtest__mutmut_17': x_run_backtest__mutmut_17, 
    'x_run_backtest__mutmut_18': x_run_backtest__mutmut_18, 
    'x_run_backtest__mutmut_19': x_run_backtest__mutmut_19, 
    'x_run_backtest__mutmut_20': x_run_backtest__mutmut_20, 
    'x_run_backtest__mutmut_21': x_run_backtest__mutmut_21, 
    'x_run_backtest__mutmut_22': x_run_backtest__mutmut_22, 
    'x_run_backtest__mutmut_23': x_run_backtest__mutmut_23, 
    'x_run_backtest__mutmut_24': x_run_backtest__mutmut_24, 
    'x_run_backtest__mutmut_25': x_run_backtest__mutmut_25, 
    'x_run_backtest__mutmut_26': x_run_backtest__mutmut_26, 
    'x_run_backtest__mutmut_27': x_run_backtest__mutmut_27, 
    'x_run_backtest__mutmut_28': x_run_backtest__mutmut_28, 
    'x_run_backtest__mutmut_29': x_run_backtest__mutmut_29, 
    'x_run_backtest__mutmut_30': x_run_backtest__mutmut_30, 
    'x_run_backtest__mutmut_31': x_run_backtest__mutmut_31, 
    'x_run_backtest__mutmut_32': x_run_backtest__mutmut_32, 
    'x_run_backtest__mutmut_33': x_run_backtest__mutmut_33, 
    'x_run_backtest__mutmut_34': x_run_backtest__mutmut_34, 
    'x_run_backtest__mutmut_35': x_run_backtest__mutmut_35, 
    'x_run_backtest__mutmut_36': x_run_backtest__mutmut_36, 
    'x_run_backtest__mutmut_37': x_run_backtest__mutmut_37, 
    'x_run_backtest__mutmut_38': x_run_backtest__mutmut_38, 
    'x_run_backtest__mutmut_39': x_run_backtest__mutmut_39, 
    'x_run_backtest__mutmut_40': x_run_backtest__mutmut_40, 
    'x_run_backtest__mutmut_41': x_run_backtest__mutmut_41, 
    'x_run_backtest__mutmut_42': x_run_backtest__mutmut_42
}
x_run_backtest__mutmut_orig.__name__ = 'x_run_backtest'
