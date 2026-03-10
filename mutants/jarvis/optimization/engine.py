# jarvis/optimization/engine.py
# Version: 1.0.0
# External optimization layer.
# External to jarvis/core/, jarvis/risk/, jarvis/utils/, jarvis/portfolio/,
# jarvis/execution/, jarvis/orchestrator/, jarvis/backtest/,
# jarvis/walkforward/, jarvis/metrics/, jarvis/report/, jarvis/strategy/
# per FAS v6.1.0 architecture rules.
#
# DETERMINISM GUARANTEE:
#   No stochastic operations. No random number generation. No sampling.
#   No external state reads. No side effects. No file I/O. No logging.
#   No environment variable access. No global mutable state.
#   Output is a pure function of inputs.
#   Iteration order over parameter combinations is fully deterministic:
#   outer loop windows, middle loop steps, inner loop meta_uncertainties.
#   No sorting is applied. Input list order is preserved exactly.
#
# PURPOSE:
#   Iterates over the Cartesian product of windows x steps x
#   meta_uncertainties and calls run_strategy() for each combination.
#   Collects structured results in a list preserving iteration order.
#   No risk logic, allocation logic, backtest logic, metric formula,
#   or strategy logic is reimplemented here.
#
# Standard import pattern:
#   from jarvis.optimization.engine import run_optimization

from jarvis.core.regime import GlobalRegimeState
from jarvis.strategy import run_strategy
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


def run_optimization(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    args = [returns_series, asset_price_series, windows, steps, meta_uncertainties, initial_capital, regime]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_run_optimization__mutmut_orig, x_run_optimization__mutmut_mutants, args, kwargs, None)


def x_run_optimization__mutmut_orig(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_1(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_2(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError(None)

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_3(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("XXwindows must not be empty.XX")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_4(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("WINDOWS MUST NOT BE EMPTY.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_5(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_6(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError(None)

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_7(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("XXsteps must not be empty.XX")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_8(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("STEPS MUST NOT BE EMPTY.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_9(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_10(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError(None)

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_11(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("XXmeta_uncertainties must not be empty.XX")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_12(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("META_UNCERTAINTIES MUST NOT BE EMPTY.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_13(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = None
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_14(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w <= 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_15(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 21]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_16(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            None
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_17(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = None
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_18(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s <= 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_19(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 2]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_20(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            None
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_21(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = None
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_22(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 and mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_23(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu <= 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_24(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 1.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_25(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu >= 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_26(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 2.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_27(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            None
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_28(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = None

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_29(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = None
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_30(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=None,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_31(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=None,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_32(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=None,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_33(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=None,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_34(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=None,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_35(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=None,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_36(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=None,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_37(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_38(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_39(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_40(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_41(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_42(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_43(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_44(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    None
                )

    return results


def x_run_optimization__mutmut_45(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "XXwindowXX": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_46(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "WINDOW": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_47(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "XXstepXX": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_48(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "STEP": step,
                        "meta_uncertainty": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_49(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "XXmeta_uncertaintyXX": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_50(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "META_UNCERTAINTY": meta_uncertainty,
                        "result": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_51(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "XXresultXX": strategy_output,
                    }
                )

    return results


def x_run_optimization__mutmut_52(
    returns_series: list[float],
    asset_price_series: list[float],
    windows: list[int],
    steps: list[int],
    meta_uncertainties: list[float],
    initial_capital: float,
    regime: GlobalRegimeState,
) -> list[dict]:
    """
    Iterate over parameter combinations and collect run_strategy() results.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        All strategy execution is delegated entirely to
        jarvis.strategy.run_strategy(). No risk, allocation, backtest,
        walkforward, metric, or strategy logic is reproduced, inlined,
        or approximated here. This function performs only parameter
        validation and iteration over the Cartesian product of the
        input parameter lists.

      PROHIBITED-01 (no stochastic operations):
        Iteration order is fully deterministic. No shuffling, no
        random sampling of parameter combinations, no probabilistic
        pruning of the search space.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.

      DET-03 (no side effects): Input lists are not mutated. All
        intermediate and output containers are constructed fresh per call.

    ITERATION ORDER CONTRACT:
      The Cartesian product is iterated as:
        for window in windows:
          for step in steps:
            for meta_uncertainty in meta_uncertainties:
      This order is fixed and deterministic. No sorting is applied at
      any stage. The output list preserves this order exactly.

    VALIDATION CONTRACT:
      All three parameter lists must be non-empty.
      All windows must be >= 20 (RiskEngine minimum).
      All steps must be >= 1.
      All meta_uncertainties must be in [0.0, 1.0].
      Validation is performed before any call to run_strategy().
      Additional ValueError may propagate from run_strategy() on
      invalid series lengths or capital values.

    Parameters
    ----------
    returns_series : list[float]
        Full sequence of per-period returns.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    asset_price_series : list[float]
        Full sequence of per-period asset prices.
        Passed unchanged to run_strategy() for every combination.
        Not mutated by this function.
    windows : list[int]
        Lookback window sizes to iterate over. Must be non-empty.
        Each value must be >= 20.
    steps : list[int]
        Step sizes to iterate over. Must be non-empty.
        Each value must be >= 1.
    meta_uncertainties : list[float]
        Meta-uncertainty values to iterate over. Must be non-empty.
        Each value must be in [0.0, 1.0].
    initial_capital : float
        Starting equity passed unchanged to run_strategy() for every
        combination. Validated downstream by run_strategy().
    regime : GlobalRegimeState
        Canonical GlobalRegimeState instance from jarvis.core.regime.
        Passed unchanged to run_strategy() for every combination.

    Returns
    -------
    list[dict]
        One entry per parameter combination in iteration order.
        Each entry is a dict with keys:
          "window"           -- int: the window value for this run.
          "step"             -- int: the step value for this run.
          "meta_uncertainty" -- float: the meta_uncertainty for this run.
          "result"           -- dict[str, object]: the full output of
                                run_strategy() for this combination,
                                containing "segments", "segment_metrics",
                                and "aggregate".
        Total length equals len(windows) * len(steps) * len(meta_uncertainties).

    Raises
    ------
    ValueError
        If windows is empty.
        If steps is empty.
        If meta_uncertainties is empty.
        If any value in windows is < 20.
        If any value in steps is < 1.
        If any value in meta_uncertainties is < 0.0 or > 1.0.
        Additional ValueError may propagate from run_strategy() on
        invalid series data or capital values.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    Input lists are not mutated. All output containers are fresh.
    periods_per_year is not exposed as a parameter in this layer.
    run_strategy() is called with its default periods_per_year=252.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if not windows:
        raise ValueError("windows must not be empty.")

    if not steps:
        raise ValueError("steps must not be empty.")

    if not meta_uncertainties:
        raise ValueError("meta_uncertainties must not be empty.")

    invalid_windows: list[int] = [w for w in windows if w < 20]
    if invalid_windows:
        raise ValueError(
            f"All windows must be >= 20 (RiskEngine minimum). "
            f"Invalid values: {invalid_windows}"
        )

    invalid_steps: list[int] = [s for s in steps if s < 1]
    if invalid_steps:
        raise ValueError(
            f"All steps must be >= 1. "
            f"Invalid values: {invalid_steps}"
        )

    invalid_mus: list[float] = [
        mu for mu in meta_uncertainties if mu < 0.0 or mu > 1.0
    ]
    if invalid_mus:
        raise ValueError(
            f"All meta_uncertainties must be in [0.0, 1.0]. "
            f"Invalid values: {invalid_mus}"
        )

    # ------------------------------------------------------------------
    # Cartesian product iteration -- order: windows x steps x meta_uncertainties.
    # ------------------------------------------------------------------
    results: list[dict] = []

    for window in windows:
        for step in steps:
            for meta_uncertainty in meta_uncertainties:
                strategy_output: dict = run_strategy(
                    returns_series=returns_series,
                    asset_price_series=asset_price_series,
                    window=window,
                    step=step,
                    initial_capital=initial_capital,
                    regime=regime,
                    meta_uncertainty=meta_uncertainty,
                )
                results.append(
                    {
                        "window": window,
                        "step": step,
                        "meta_uncertainty": meta_uncertainty,
                        "RESULT": strategy_output,
                    }
                )

    return results

x_run_optimization__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_run_optimization__mutmut_1': x_run_optimization__mutmut_1, 
    'x_run_optimization__mutmut_2': x_run_optimization__mutmut_2, 
    'x_run_optimization__mutmut_3': x_run_optimization__mutmut_3, 
    'x_run_optimization__mutmut_4': x_run_optimization__mutmut_4, 
    'x_run_optimization__mutmut_5': x_run_optimization__mutmut_5, 
    'x_run_optimization__mutmut_6': x_run_optimization__mutmut_6, 
    'x_run_optimization__mutmut_7': x_run_optimization__mutmut_7, 
    'x_run_optimization__mutmut_8': x_run_optimization__mutmut_8, 
    'x_run_optimization__mutmut_9': x_run_optimization__mutmut_9, 
    'x_run_optimization__mutmut_10': x_run_optimization__mutmut_10, 
    'x_run_optimization__mutmut_11': x_run_optimization__mutmut_11, 
    'x_run_optimization__mutmut_12': x_run_optimization__mutmut_12, 
    'x_run_optimization__mutmut_13': x_run_optimization__mutmut_13, 
    'x_run_optimization__mutmut_14': x_run_optimization__mutmut_14, 
    'x_run_optimization__mutmut_15': x_run_optimization__mutmut_15, 
    'x_run_optimization__mutmut_16': x_run_optimization__mutmut_16, 
    'x_run_optimization__mutmut_17': x_run_optimization__mutmut_17, 
    'x_run_optimization__mutmut_18': x_run_optimization__mutmut_18, 
    'x_run_optimization__mutmut_19': x_run_optimization__mutmut_19, 
    'x_run_optimization__mutmut_20': x_run_optimization__mutmut_20, 
    'x_run_optimization__mutmut_21': x_run_optimization__mutmut_21, 
    'x_run_optimization__mutmut_22': x_run_optimization__mutmut_22, 
    'x_run_optimization__mutmut_23': x_run_optimization__mutmut_23, 
    'x_run_optimization__mutmut_24': x_run_optimization__mutmut_24, 
    'x_run_optimization__mutmut_25': x_run_optimization__mutmut_25, 
    'x_run_optimization__mutmut_26': x_run_optimization__mutmut_26, 
    'x_run_optimization__mutmut_27': x_run_optimization__mutmut_27, 
    'x_run_optimization__mutmut_28': x_run_optimization__mutmut_28, 
    'x_run_optimization__mutmut_29': x_run_optimization__mutmut_29, 
    'x_run_optimization__mutmut_30': x_run_optimization__mutmut_30, 
    'x_run_optimization__mutmut_31': x_run_optimization__mutmut_31, 
    'x_run_optimization__mutmut_32': x_run_optimization__mutmut_32, 
    'x_run_optimization__mutmut_33': x_run_optimization__mutmut_33, 
    'x_run_optimization__mutmut_34': x_run_optimization__mutmut_34, 
    'x_run_optimization__mutmut_35': x_run_optimization__mutmut_35, 
    'x_run_optimization__mutmut_36': x_run_optimization__mutmut_36, 
    'x_run_optimization__mutmut_37': x_run_optimization__mutmut_37, 
    'x_run_optimization__mutmut_38': x_run_optimization__mutmut_38, 
    'x_run_optimization__mutmut_39': x_run_optimization__mutmut_39, 
    'x_run_optimization__mutmut_40': x_run_optimization__mutmut_40, 
    'x_run_optimization__mutmut_41': x_run_optimization__mutmut_41, 
    'x_run_optimization__mutmut_42': x_run_optimization__mutmut_42, 
    'x_run_optimization__mutmut_43': x_run_optimization__mutmut_43, 
    'x_run_optimization__mutmut_44': x_run_optimization__mutmut_44, 
    'x_run_optimization__mutmut_45': x_run_optimization__mutmut_45, 
    'x_run_optimization__mutmut_46': x_run_optimization__mutmut_46, 
    'x_run_optimization__mutmut_47': x_run_optimization__mutmut_47, 
    'x_run_optimization__mutmut_48': x_run_optimization__mutmut_48, 
    'x_run_optimization__mutmut_49': x_run_optimization__mutmut_49, 
    'x_run_optimization__mutmut_50': x_run_optimization__mutmut_50, 
    'x_run_optimization__mutmut_51': x_run_optimization__mutmut_51, 
    'x_run_optimization__mutmut_52': x_run_optimization__mutmut_52
}
x_run_optimization__mutmut_orig.__name__ = 'x_run_optimization'
