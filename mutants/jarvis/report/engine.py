# jarvis/report/engine.py
# Version: 1.0.0
# External report layer.
# External to jarvis/core/, jarvis/risk/, jarvis/utils/, jarvis/portfolio/,
# jarvis/execution/, jarvis/orchestrator/, jarvis/backtest/,
# jarvis/walkforward/, jarvis/metrics/ per FAS v6.1.0 architecture rules.
#
# DETERMINISM GUARANTEE:
#   No stochastic operations. No random number generation. No sampling.
#   No external state reads. No side effects. No file I/O. No logging.
#   No environment variable access. No global mutable state.
#   Output is a pure function of inputs.
#
# PURPOSE:
#   Assembles a structured report dict by delegating metric computation
#   entirely to compute_metrics(). No metric logic is reimplemented here.
#   The equity_curve is included in the output unchanged and uncopied --
#   callers must treat it as read-only per the no-mutation contract.
#
# Standard import pattern:
#   from jarvis.report.engine import generate_report

from jarvis.metrics import compute_metrics
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


def generate_report(
    equity_curve: list[float],
    periods_per_year: int = 252,
) -> dict[str, object]:
    args = [equity_curve, periods_per_year]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_generate_report__mutmut_orig, x_generate_report__mutmut_mutants, args, kwargs, None)


def x_generate_report__mutmut_orig(
    equity_curve: list[float],
    periods_per_year: int = 252,
) -> dict[str, object]:
    """
    Assemble a structured performance report from an equity curve.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation): All metric computation is
        delegated exclusively to jarvis.metrics.compute_metrics().
        No formula from that module is reproduced, inlined, or
        approximated here.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.
        No module-level or class-level state is read during execution.

      DET-03 (no side effects): The equity_curve argument is not mutated.
        The returned dict contains a reference to the original list, not
        a copy. Callers must treat the contained equity_curve as read-only.

    Parameters
    ----------
    equity_curve : list[float]
        Sequence of portfolio equity values.
        Must contain at least 2 values.
        All values must be strictly positive.
        Validated here (length >= 2) and downstream by compute_metrics()
        (positivity and length).
        Not mutated by this function.
    periods_per_year : int
        Annualization factor passed unchanged to compute_metrics().
        Default = 252.

    Returns
    -------
    dict[str, object]
        Structured report containing:
          "equity_curve"    -- the original equity_curve list (unmodified).
          "metrics"         -- dict[str, float] returned by compute_metrics().
                               Keys: total_return, cagr, volatility,
                                     sharpe, max_drawdown.
          "periods_per_year" -- the periods_per_year value used.

    Raises
    ------
    ValueError
        If len(equity_curve) < 2 (validated here before delegation).
        Additional ValueError may propagate from compute_metrics() if
        any equity value is <= 0 or the annualization period is invalid.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if len(equity_curve) < 2:
        raise ValueError(
            f"equity_curve must contain at least 2 values. "
            f"Received: {len(equity_curve)}"
        )

    metrics: dict[str, float] = compute_metrics(
        equity_curve=equity_curve,
        periods_per_year=periods_per_year,
    )

    return {
        "equity_curve": equity_curve,
        "metrics": metrics,
        "periods_per_year": periods_per_year,
    }


def x_generate_report__mutmut_1(
    equity_curve: list[float],
    periods_per_year: int = 253,
) -> dict[str, object]:
    """
    Assemble a structured performance report from an equity curve.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation): All metric computation is
        delegated exclusively to jarvis.metrics.compute_metrics().
        No formula from that module is reproduced, inlined, or
        approximated here.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.
        No module-level or class-level state is read during execution.

      DET-03 (no side effects): The equity_curve argument is not mutated.
        The returned dict contains a reference to the original list, not
        a copy. Callers must treat the contained equity_curve as read-only.

    Parameters
    ----------
    equity_curve : list[float]
        Sequence of portfolio equity values.
        Must contain at least 2 values.
        All values must be strictly positive.
        Validated here (length >= 2) and downstream by compute_metrics()
        (positivity and length).
        Not mutated by this function.
    periods_per_year : int
        Annualization factor passed unchanged to compute_metrics().
        Default = 252.

    Returns
    -------
    dict[str, object]
        Structured report containing:
          "equity_curve"    -- the original equity_curve list (unmodified).
          "metrics"         -- dict[str, float] returned by compute_metrics().
                               Keys: total_return, cagr, volatility,
                                     sharpe, max_drawdown.
          "periods_per_year" -- the periods_per_year value used.

    Raises
    ------
    ValueError
        If len(equity_curve) < 2 (validated here before delegation).
        Additional ValueError may propagate from compute_metrics() if
        any equity value is <= 0 or the annualization period is invalid.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if len(equity_curve) < 2:
        raise ValueError(
            f"equity_curve must contain at least 2 values. "
            f"Received: {len(equity_curve)}"
        )

    metrics: dict[str, float] = compute_metrics(
        equity_curve=equity_curve,
        periods_per_year=periods_per_year,
    )

    return {
        "equity_curve": equity_curve,
        "metrics": metrics,
        "periods_per_year": periods_per_year,
    }


def x_generate_report__mutmut_2(
    equity_curve: list[float],
    periods_per_year: int = 252,
) -> dict[str, object]:
    """
    Assemble a structured performance report from an equity curve.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation): All metric computation is
        delegated exclusively to jarvis.metrics.compute_metrics().
        No formula from that module is reproduced, inlined, or
        approximated here.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.
        No module-level or class-level state is read during execution.

      DET-03 (no side effects): The equity_curve argument is not mutated.
        The returned dict contains a reference to the original list, not
        a copy. Callers must treat the contained equity_curve as read-only.

    Parameters
    ----------
    equity_curve : list[float]
        Sequence of portfolio equity values.
        Must contain at least 2 values.
        All values must be strictly positive.
        Validated here (length >= 2) and downstream by compute_metrics()
        (positivity and length).
        Not mutated by this function.
    periods_per_year : int
        Annualization factor passed unchanged to compute_metrics().
        Default = 252.

    Returns
    -------
    dict[str, object]
        Structured report containing:
          "equity_curve"    -- the original equity_curve list (unmodified).
          "metrics"         -- dict[str, float] returned by compute_metrics().
                               Keys: total_return, cagr, volatility,
                                     sharpe, max_drawdown.
          "periods_per_year" -- the periods_per_year value used.

    Raises
    ------
    ValueError
        If len(equity_curve) < 2 (validated here before delegation).
        Additional ValueError may propagate from compute_metrics() if
        any equity value is <= 0 or the annualization period is invalid.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if len(equity_curve) <= 2:
        raise ValueError(
            f"equity_curve must contain at least 2 values. "
            f"Received: {len(equity_curve)}"
        )

    metrics: dict[str, float] = compute_metrics(
        equity_curve=equity_curve,
        periods_per_year=periods_per_year,
    )

    return {
        "equity_curve": equity_curve,
        "metrics": metrics,
        "periods_per_year": periods_per_year,
    }


def x_generate_report__mutmut_3(
    equity_curve: list[float],
    periods_per_year: int = 252,
) -> dict[str, object]:
    """
    Assemble a structured performance report from an equity curve.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation): All metric computation is
        delegated exclusively to jarvis.metrics.compute_metrics().
        No formula from that module is reproduced, inlined, or
        approximated here.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.
        No module-level or class-level state is read during execution.

      DET-03 (no side effects): The equity_curve argument is not mutated.
        The returned dict contains a reference to the original list, not
        a copy. Callers must treat the contained equity_curve as read-only.

    Parameters
    ----------
    equity_curve : list[float]
        Sequence of portfolio equity values.
        Must contain at least 2 values.
        All values must be strictly positive.
        Validated here (length >= 2) and downstream by compute_metrics()
        (positivity and length).
        Not mutated by this function.
    periods_per_year : int
        Annualization factor passed unchanged to compute_metrics().
        Default = 252.

    Returns
    -------
    dict[str, object]
        Structured report containing:
          "equity_curve"    -- the original equity_curve list (unmodified).
          "metrics"         -- dict[str, float] returned by compute_metrics().
                               Keys: total_return, cagr, volatility,
                                     sharpe, max_drawdown.
          "periods_per_year" -- the periods_per_year value used.

    Raises
    ------
    ValueError
        If len(equity_curve) < 2 (validated here before delegation).
        Additional ValueError may propagate from compute_metrics() if
        any equity value is <= 0 or the annualization period is invalid.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if len(equity_curve) < 3:
        raise ValueError(
            f"equity_curve must contain at least 2 values. "
            f"Received: {len(equity_curve)}"
        )

    metrics: dict[str, float] = compute_metrics(
        equity_curve=equity_curve,
        periods_per_year=periods_per_year,
    )

    return {
        "equity_curve": equity_curve,
        "metrics": metrics,
        "periods_per_year": periods_per_year,
    }


def x_generate_report__mutmut_4(
    equity_curve: list[float],
    periods_per_year: int = 252,
) -> dict[str, object]:
    """
    Assemble a structured performance report from an equity curve.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation): All metric computation is
        delegated exclusively to jarvis.metrics.compute_metrics().
        No formula from that module is reproduced, inlined, or
        approximated here.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.
        No module-level or class-level state is read during execution.

      DET-03 (no side effects): The equity_curve argument is not mutated.
        The returned dict contains a reference to the original list, not
        a copy. Callers must treat the contained equity_curve as read-only.

    Parameters
    ----------
    equity_curve : list[float]
        Sequence of portfolio equity values.
        Must contain at least 2 values.
        All values must be strictly positive.
        Validated here (length >= 2) and downstream by compute_metrics()
        (positivity and length).
        Not mutated by this function.
    periods_per_year : int
        Annualization factor passed unchanged to compute_metrics().
        Default = 252.

    Returns
    -------
    dict[str, object]
        Structured report containing:
          "equity_curve"    -- the original equity_curve list (unmodified).
          "metrics"         -- dict[str, float] returned by compute_metrics().
                               Keys: total_return, cagr, volatility,
                                     sharpe, max_drawdown.
          "periods_per_year" -- the periods_per_year value used.

    Raises
    ------
    ValueError
        If len(equity_curve) < 2 (validated here before delegation).
        Additional ValueError may propagate from compute_metrics() if
        any equity value is <= 0 or the annualization period is invalid.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if len(equity_curve) < 2:
        raise ValueError(
            None
        )

    metrics: dict[str, float] = compute_metrics(
        equity_curve=equity_curve,
        periods_per_year=periods_per_year,
    )

    return {
        "equity_curve": equity_curve,
        "metrics": metrics,
        "periods_per_year": periods_per_year,
    }


def x_generate_report__mutmut_5(
    equity_curve: list[float],
    periods_per_year: int = 252,
) -> dict[str, object]:
    """
    Assemble a structured performance report from an equity curve.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation): All metric computation is
        delegated exclusively to jarvis.metrics.compute_metrics().
        No formula from that module is reproduced, inlined, or
        approximated here.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.
        No module-level or class-level state is read during execution.

      DET-03 (no side effects): The equity_curve argument is not mutated.
        The returned dict contains a reference to the original list, not
        a copy. Callers must treat the contained equity_curve as read-only.

    Parameters
    ----------
    equity_curve : list[float]
        Sequence of portfolio equity values.
        Must contain at least 2 values.
        All values must be strictly positive.
        Validated here (length >= 2) and downstream by compute_metrics()
        (positivity and length).
        Not mutated by this function.
    periods_per_year : int
        Annualization factor passed unchanged to compute_metrics().
        Default = 252.

    Returns
    -------
    dict[str, object]
        Structured report containing:
          "equity_curve"    -- the original equity_curve list (unmodified).
          "metrics"         -- dict[str, float] returned by compute_metrics().
                               Keys: total_return, cagr, volatility,
                                     sharpe, max_drawdown.
          "periods_per_year" -- the periods_per_year value used.

    Raises
    ------
    ValueError
        If len(equity_curve) < 2 (validated here before delegation).
        Additional ValueError may propagate from compute_metrics() if
        any equity value is <= 0 or the annualization period is invalid.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if len(equity_curve) < 2:
        raise ValueError(
            f"equity_curve must contain at least 2 values. "
            f"Received: {len(equity_curve)}"
        )

    metrics: dict[str, float] = None

    return {
        "equity_curve": equity_curve,
        "metrics": metrics,
        "periods_per_year": periods_per_year,
    }


def x_generate_report__mutmut_6(
    equity_curve: list[float],
    periods_per_year: int = 252,
) -> dict[str, object]:
    """
    Assemble a structured performance report from an equity curve.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation): All metric computation is
        delegated exclusively to jarvis.metrics.compute_metrics().
        No formula from that module is reproduced, inlined, or
        approximated here.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.
        No module-level or class-level state is read during execution.

      DET-03 (no side effects): The equity_curve argument is not mutated.
        The returned dict contains a reference to the original list, not
        a copy. Callers must treat the contained equity_curve as read-only.

    Parameters
    ----------
    equity_curve : list[float]
        Sequence of portfolio equity values.
        Must contain at least 2 values.
        All values must be strictly positive.
        Validated here (length >= 2) and downstream by compute_metrics()
        (positivity and length).
        Not mutated by this function.
    periods_per_year : int
        Annualization factor passed unchanged to compute_metrics().
        Default = 252.

    Returns
    -------
    dict[str, object]
        Structured report containing:
          "equity_curve"    -- the original equity_curve list (unmodified).
          "metrics"         -- dict[str, float] returned by compute_metrics().
                               Keys: total_return, cagr, volatility,
                                     sharpe, max_drawdown.
          "periods_per_year" -- the periods_per_year value used.

    Raises
    ------
    ValueError
        If len(equity_curve) < 2 (validated here before delegation).
        Additional ValueError may propagate from compute_metrics() if
        any equity value is <= 0 or the annualization period is invalid.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if len(equity_curve) < 2:
        raise ValueError(
            f"equity_curve must contain at least 2 values. "
            f"Received: {len(equity_curve)}"
        )

    metrics: dict[str, float] = compute_metrics(
        equity_curve=None,
        periods_per_year=periods_per_year,
    )

    return {
        "equity_curve": equity_curve,
        "metrics": metrics,
        "periods_per_year": periods_per_year,
    }


def x_generate_report__mutmut_7(
    equity_curve: list[float],
    periods_per_year: int = 252,
) -> dict[str, object]:
    """
    Assemble a structured performance report from an equity curve.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation): All metric computation is
        delegated exclusively to jarvis.metrics.compute_metrics().
        No formula from that module is reproduced, inlined, or
        approximated here.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.
        No module-level or class-level state is read during execution.

      DET-03 (no side effects): The equity_curve argument is not mutated.
        The returned dict contains a reference to the original list, not
        a copy. Callers must treat the contained equity_curve as read-only.

    Parameters
    ----------
    equity_curve : list[float]
        Sequence of portfolio equity values.
        Must contain at least 2 values.
        All values must be strictly positive.
        Validated here (length >= 2) and downstream by compute_metrics()
        (positivity and length).
        Not mutated by this function.
    periods_per_year : int
        Annualization factor passed unchanged to compute_metrics().
        Default = 252.

    Returns
    -------
    dict[str, object]
        Structured report containing:
          "equity_curve"    -- the original equity_curve list (unmodified).
          "metrics"         -- dict[str, float] returned by compute_metrics().
                               Keys: total_return, cagr, volatility,
                                     sharpe, max_drawdown.
          "periods_per_year" -- the periods_per_year value used.

    Raises
    ------
    ValueError
        If len(equity_curve) < 2 (validated here before delegation).
        Additional ValueError may propagate from compute_metrics() if
        any equity value is <= 0 or the annualization period is invalid.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if len(equity_curve) < 2:
        raise ValueError(
            f"equity_curve must contain at least 2 values. "
            f"Received: {len(equity_curve)}"
        )

    metrics: dict[str, float] = compute_metrics(
        equity_curve=equity_curve,
        periods_per_year=None,
    )

    return {
        "equity_curve": equity_curve,
        "metrics": metrics,
        "periods_per_year": periods_per_year,
    }


def x_generate_report__mutmut_8(
    equity_curve: list[float],
    periods_per_year: int = 252,
) -> dict[str, object]:
    """
    Assemble a structured performance report from an equity curve.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation): All metric computation is
        delegated exclusively to jarvis.metrics.compute_metrics().
        No formula from that module is reproduced, inlined, or
        approximated here.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.
        No module-level or class-level state is read during execution.

      DET-03 (no side effects): The equity_curve argument is not mutated.
        The returned dict contains a reference to the original list, not
        a copy. Callers must treat the contained equity_curve as read-only.

    Parameters
    ----------
    equity_curve : list[float]
        Sequence of portfolio equity values.
        Must contain at least 2 values.
        All values must be strictly positive.
        Validated here (length >= 2) and downstream by compute_metrics()
        (positivity and length).
        Not mutated by this function.
    periods_per_year : int
        Annualization factor passed unchanged to compute_metrics().
        Default = 252.

    Returns
    -------
    dict[str, object]
        Structured report containing:
          "equity_curve"    -- the original equity_curve list (unmodified).
          "metrics"         -- dict[str, float] returned by compute_metrics().
                               Keys: total_return, cagr, volatility,
                                     sharpe, max_drawdown.
          "periods_per_year" -- the periods_per_year value used.

    Raises
    ------
    ValueError
        If len(equity_curve) < 2 (validated here before delegation).
        Additional ValueError may propagate from compute_metrics() if
        any equity value is <= 0 or the annualization period is invalid.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if len(equity_curve) < 2:
        raise ValueError(
            f"equity_curve must contain at least 2 values. "
            f"Received: {len(equity_curve)}"
        )

    metrics: dict[str, float] = compute_metrics(
        periods_per_year=periods_per_year,
    )

    return {
        "equity_curve": equity_curve,
        "metrics": metrics,
        "periods_per_year": periods_per_year,
    }


def x_generate_report__mutmut_9(
    equity_curve: list[float],
    periods_per_year: int = 252,
) -> dict[str, object]:
    """
    Assemble a structured performance report from an equity curve.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation): All metric computation is
        delegated exclusively to jarvis.metrics.compute_metrics().
        No formula from that module is reproduced, inlined, or
        approximated here.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.
        No module-level or class-level state is read during execution.

      DET-03 (no side effects): The equity_curve argument is not mutated.
        The returned dict contains a reference to the original list, not
        a copy. Callers must treat the contained equity_curve as read-only.

    Parameters
    ----------
    equity_curve : list[float]
        Sequence of portfolio equity values.
        Must contain at least 2 values.
        All values must be strictly positive.
        Validated here (length >= 2) and downstream by compute_metrics()
        (positivity and length).
        Not mutated by this function.
    periods_per_year : int
        Annualization factor passed unchanged to compute_metrics().
        Default = 252.

    Returns
    -------
    dict[str, object]
        Structured report containing:
          "equity_curve"    -- the original equity_curve list (unmodified).
          "metrics"         -- dict[str, float] returned by compute_metrics().
                               Keys: total_return, cagr, volatility,
                                     sharpe, max_drawdown.
          "periods_per_year" -- the periods_per_year value used.

    Raises
    ------
    ValueError
        If len(equity_curve) < 2 (validated here before delegation).
        Additional ValueError may propagate from compute_metrics() if
        any equity value is <= 0 or the annualization period is invalid.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if len(equity_curve) < 2:
        raise ValueError(
            f"equity_curve must contain at least 2 values. "
            f"Received: {len(equity_curve)}"
        )

    metrics: dict[str, float] = compute_metrics(
        equity_curve=equity_curve,
        )

    return {
        "equity_curve": equity_curve,
        "metrics": metrics,
        "periods_per_year": periods_per_year,
    }


def x_generate_report__mutmut_10(
    equity_curve: list[float],
    periods_per_year: int = 252,
) -> dict[str, object]:
    """
    Assemble a structured performance report from an equity curve.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation): All metric computation is
        delegated exclusively to jarvis.metrics.compute_metrics().
        No formula from that module is reproduced, inlined, or
        approximated here.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.
        No module-level or class-level state is read during execution.

      DET-03 (no side effects): The equity_curve argument is not mutated.
        The returned dict contains a reference to the original list, not
        a copy. Callers must treat the contained equity_curve as read-only.

    Parameters
    ----------
    equity_curve : list[float]
        Sequence of portfolio equity values.
        Must contain at least 2 values.
        All values must be strictly positive.
        Validated here (length >= 2) and downstream by compute_metrics()
        (positivity and length).
        Not mutated by this function.
    periods_per_year : int
        Annualization factor passed unchanged to compute_metrics().
        Default = 252.

    Returns
    -------
    dict[str, object]
        Structured report containing:
          "equity_curve"    -- the original equity_curve list (unmodified).
          "metrics"         -- dict[str, float] returned by compute_metrics().
                               Keys: total_return, cagr, volatility,
                                     sharpe, max_drawdown.
          "periods_per_year" -- the periods_per_year value used.

    Raises
    ------
    ValueError
        If len(equity_curve) < 2 (validated here before delegation).
        Additional ValueError may propagate from compute_metrics() if
        any equity value is <= 0 or the annualization period is invalid.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if len(equity_curve) < 2:
        raise ValueError(
            f"equity_curve must contain at least 2 values. "
            f"Received: {len(equity_curve)}"
        )

    metrics: dict[str, float] = compute_metrics(
        equity_curve=equity_curve,
        periods_per_year=periods_per_year,
    )

    return {
        "XXequity_curveXX": equity_curve,
        "metrics": metrics,
        "periods_per_year": periods_per_year,
    }


def x_generate_report__mutmut_11(
    equity_curve: list[float],
    periods_per_year: int = 252,
) -> dict[str, object]:
    """
    Assemble a structured performance report from an equity curve.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation): All metric computation is
        delegated exclusively to jarvis.metrics.compute_metrics().
        No formula from that module is reproduced, inlined, or
        approximated here.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.
        No module-level or class-level state is read during execution.

      DET-03 (no side effects): The equity_curve argument is not mutated.
        The returned dict contains a reference to the original list, not
        a copy. Callers must treat the contained equity_curve as read-only.

    Parameters
    ----------
    equity_curve : list[float]
        Sequence of portfolio equity values.
        Must contain at least 2 values.
        All values must be strictly positive.
        Validated here (length >= 2) and downstream by compute_metrics()
        (positivity and length).
        Not mutated by this function.
    periods_per_year : int
        Annualization factor passed unchanged to compute_metrics().
        Default = 252.

    Returns
    -------
    dict[str, object]
        Structured report containing:
          "equity_curve"    -- the original equity_curve list (unmodified).
          "metrics"         -- dict[str, float] returned by compute_metrics().
                               Keys: total_return, cagr, volatility,
                                     sharpe, max_drawdown.
          "periods_per_year" -- the periods_per_year value used.

    Raises
    ------
    ValueError
        If len(equity_curve) < 2 (validated here before delegation).
        Additional ValueError may propagate from compute_metrics() if
        any equity value is <= 0 or the annualization period is invalid.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if len(equity_curve) < 2:
        raise ValueError(
            f"equity_curve must contain at least 2 values. "
            f"Received: {len(equity_curve)}"
        )

    metrics: dict[str, float] = compute_metrics(
        equity_curve=equity_curve,
        periods_per_year=periods_per_year,
    )

    return {
        "EQUITY_CURVE": equity_curve,
        "metrics": metrics,
        "periods_per_year": periods_per_year,
    }


def x_generate_report__mutmut_12(
    equity_curve: list[float],
    periods_per_year: int = 252,
) -> dict[str, object]:
    """
    Assemble a structured performance report from an equity curve.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation): All metric computation is
        delegated exclusively to jarvis.metrics.compute_metrics().
        No formula from that module is reproduced, inlined, or
        approximated here.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.
        No module-level or class-level state is read during execution.

      DET-03 (no side effects): The equity_curve argument is not mutated.
        The returned dict contains a reference to the original list, not
        a copy. Callers must treat the contained equity_curve as read-only.

    Parameters
    ----------
    equity_curve : list[float]
        Sequence of portfolio equity values.
        Must contain at least 2 values.
        All values must be strictly positive.
        Validated here (length >= 2) and downstream by compute_metrics()
        (positivity and length).
        Not mutated by this function.
    periods_per_year : int
        Annualization factor passed unchanged to compute_metrics().
        Default = 252.

    Returns
    -------
    dict[str, object]
        Structured report containing:
          "equity_curve"    -- the original equity_curve list (unmodified).
          "metrics"         -- dict[str, float] returned by compute_metrics().
                               Keys: total_return, cagr, volatility,
                                     sharpe, max_drawdown.
          "periods_per_year" -- the periods_per_year value used.

    Raises
    ------
    ValueError
        If len(equity_curve) < 2 (validated here before delegation).
        Additional ValueError may propagate from compute_metrics() if
        any equity value is <= 0 or the annualization period is invalid.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if len(equity_curve) < 2:
        raise ValueError(
            f"equity_curve must contain at least 2 values. "
            f"Received: {len(equity_curve)}"
        )

    metrics: dict[str, float] = compute_metrics(
        equity_curve=equity_curve,
        periods_per_year=periods_per_year,
    )

    return {
        "equity_curve": equity_curve,
        "XXmetricsXX": metrics,
        "periods_per_year": periods_per_year,
    }


def x_generate_report__mutmut_13(
    equity_curve: list[float],
    periods_per_year: int = 252,
) -> dict[str, object]:
    """
    Assemble a structured performance report from an equity curve.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation): All metric computation is
        delegated exclusively to jarvis.metrics.compute_metrics().
        No formula from that module is reproduced, inlined, or
        approximated here.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.
        No module-level or class-level state is read during execution.

      DET-03 (no side effects): The equity_curve argument is not mutated.
        The returned dict contains a reference to the original list, not
        a copy. Callers must treat the contained equity_curve as read-only.

    Parameters
    ----------
    equity_curve : list[float]
        Sequence of portfolio equity values.
        Must contain at least 2 values.
        All values must be strictly positive.
        Validated here (length >= 2) and downstream by compute_metrics()
        (positivity and length).
        Not mutated by this function.
    periods_per_year : int
        Annualization factor passed unchanged to compute_metrics().
        Default = 252.

    Returns
    -------
    dict[str, object]
        Structured report containing:
          "equity_curve"    -- the original equity_curve list (unmodified).
          "metrics"         -- dict[str, float] returned by compute_metrics().
                               Keys: total_return, cagr, volatility,
                                     sharpe, max_drawdown.
          "periods_per_year" -- the periods_per_year value used.

    Raises
    ------
    ValueError
        If len(equity_curve) < 2 (validated here before delegation).
        Additional ValueError may propagate from compute_metrics() if
        any equity value is <= 0 or the annualization period is invalid.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if len(equity_curve) < 2:
        raise ValueError(
            f"equity_curve must contain at least 2 values. "
            f"Received: {len(equity_curve)}"
        )

    metrics: dict[str, float] = compute_metrics(
        equity_curve=equity_curve,
        periods_per_year=periods_per_year,
    )

    return {
        "equity_curve": equity_curve,
        "METRICS": metrics,
        "periods_per_year": periods_per_year,
    }


def x_generate_report__mutmut_14(
    equity_curve: list[float],
    periods_per_year: int = 252,
) -> dict[str, object]:
    """
    Assemble a structured performance report from an equity curve.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation): All metric computation is
        delegated exclusively to jarvis.metrics.compute_metrics().
        No formula from that module is reproduced, inlined, or
        approximated here.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.
        No module-level or class-level state is read during execution.

      DET-03 (no side effects): The equity_curve argument is not mutated.
        The returned dict contains a reference to the original list, not
        a copy. Callers must treat the contained equity_curve as read-only.

    Parameters
    ----------
    equity_curve : list[float]
        Sequence of portfolio equity values.
        Must contain at least 2 values.
        All values must be strictly positive.
        Validated here (length >= 2) and downstream by compute_metrics()
        (positivity and length).
        Not mutated by this function.
    periods_per_year : int
        Annualization factor passed unchanged to compute_metrics().
        Default = 252.

    Returns
    -------
    dict[str, object]
        Structured report containing:
          "equity_curve"    -- the original equity_curve list (unmodified).
          "metrics"         -- dict[str, float] returned by compute_metrics().
                               Keys: total_return, cagr, volatility,
                                     sharpe, max_drawdown.
          "periods_per_year" -- the periods_per_year value used.

    Raises
    ------
    ValueError
        If len(equity_curve) < 2 (validated here before delegation).
        Additional ValueError may propagate from compute_metrics() if
        any equity value is <= 0 or the annualization period is invalid.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if len(equity_curve) < 2:
        raise ValueError(
            f"equity_curve must contain at least 2 values. "
            f"Received: {len(equity_curve)}"
        )

    metrics: dict[str, float] = compute_metrics(
        equity_curve=equity_curve,
        periods_per_year=periods_per_year,
    )

    return {
        "equity_curve": equity_curve,
        "metrics": metrics,
        "XXperiods_per_yearXX": periods_per_year,
    }


def x_generate_report__mutmut_15(
    equity_curve: list[float],
    periods_per_year: int = 252,
) -> dict[str, object]:
    """
    Assemble a structured performance report from an equity curve.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation): All metric computation is
        delegated exclusively to jarvis.metrics.compute_metrics().
        No formula from that module is reproduced, inlined, or
        approximated here.

      PROHIBITED-02 (no file I/O): No file is read or written.

      PROHIBITED-03 (no logging): No logging calls are made.

      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.

      DET-02 (no external state reads): All inputs are passed explicitly.
        No module-level or class-level state is read during execution.

      DET-03 (no side effects): The equity_curve argument is not mutated.
        The returned dict contains a reference to the original list, not
        a copy. Callers must treat the contained equity_curve as read-only.

    Parameters
    ----------
    equity_curve : list[float]
        Sequence of portfolio equity values.
        Must contain at least 2 values.
        All values must be strictly positive.
        Validated here (length >= 2) and downstream by compute_metrics()
        (positivity and length).
        Not mutated by this function.
    periods_per_year : int
        Annualization factor passed unchanged to compute_metrics().
        Default = 252.

    Returns
    -------
    dict[str, object]
        Structured report containing:
          "equity_curve"    -- the original equity_curve list (unmodified).
          "metrics"         -- dict[str, float] returned by compute_metrics().
                               Keys: total_return, cagr, volatility,
                                     sharpe, max_drawdown.
          "periods_per_year" -- the periods_per_year value used.

    Raises
    ------
    ValueError
        If len(equity_curve) < 2 (validated here before delegation).
        Additional ValueError may propagate from compute_metrics() if
        any equity value is <= 0 or the annualization period is invalid.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if len(equity_curve) < 2:
        raise ValueError(
            f"equity_curve must contain at least 2 values. "
            f"Received: {len(equity_curve)}"
        )

    metrics: dict[str, float] = compute_metrics(
        equity_curve=equity_curve,
        periods_per_year=periods_per_year,
    )

    return {
        "equity_curve": equity_curve,
        "metrics": metrics,
        "PERIODS_PER_YEAR": periods_per_year,
    }

x_generate_report__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_generate_report__mutmut_1': x_generate_report__mutmut_1, 
    'x_generate_report__mutmut_2': x_generate_report__mutmut_2, 
    'x_generate_report__mutmut_3': x_generate_report__mutmut_3, 
    'x_generate_report__mutmut_4': x_generate_report__mutmut_4, 
    'x_generate_report__mutmut_5': x_generate_report__mutmut_5, 
    'x_generate_report__mutmut_6': x_generate_report__mutmut_6, 
    'x_generate_report__mutmut_7': x_generate_report__mutmut_7, 
    'x_generate_report__mutmut_8': x_generate_report__mutmut_8, 
    'x_generate_report__mutmut_9': x_generate_report__mutmut_9, 
    'x_generate_report__mutmut_10': x_generate_report__mutmut_10, 
    'x_generate_report__mutmut_11': x_generate_report__mutmut_11, 
    'x_generate_report__mutmut_12': x_generate_report__mutmut_12, 
    'x_generate_report__mutmut_13': x_generate_report__mutmut_13, 
    'x_generate_report__mutmut_14': x_generate_report__mutmut_14, 
    'x_generate_report__mutmut_15': x_generate_report__mutmut_15
}
x_generate_report__mutmut_orig.__name__ = 'x_generate_report'
