# jarvis/robustness/engine.py
# Version: 1.0.0
# External robustness evaluation layer.
# External to jarvis/core/, jarvis/risk/, jarvis/utils/, jarvis/portfolio/,
# jarvis/execution/, jarvis/orchestrator/, jarvis/backtest/,
# jarvis/walkforward/, jarvis/metrics/, jarvis/report/, jarvis/strategy/,
# jarvis/optimization/, jarvis/selection/ per FAS v6.1.0 architecture rules.
#
# DETERMINISM GUARANTEE:
#   No stochastic operations. No random number generation. No sampling.
#   No external state reads. No side effects. No file I/O. No logging.
#   No environment variable access. No global mutable state.
#   Output is a pure function of inputs.
#
# FAS ARCHITECTURE POSITION:
#   External to all other layers.
#   Consumes output of jarvis.selection.run_selection() only.
#   No calls to any other layer are made.
#
# INPUT CONTRACT NOTE:
#   run_selection() produces ranking entries with flat keys:
#     "window", "step", "meta_uncertainty", "aggregate", "score_tuple"
#   and top-level keys: "best_params", "best_score", "ranking".
#   This module reads those keys directly. "best_params" is the
#   canonical params dict. ranking[0] is the best entry.
#
# Standard import pattern:
#   from jarvis.robustness.engine import evaluate_robustness

from typing import Any
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


def evaluate_robustness(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    args = [selection_output]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_evaluate_robustness__mutmut_orig, x_evaluate_robustness__mutmut_mutants, args, kwargs, None)


def x_evaluate_robustness__mutmut_orig(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_1(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = None

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_2(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["XXrankingXX"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_3(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["RANKING"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_4(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) != 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_5(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 1:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_6(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError(None)

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_7(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("XXranking must not be empty.XX")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_8(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("RANKING MUST NOT BE EMPTY.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_9(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = None
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_10(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[1]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_11(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = None

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_12(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "XXwindowXX":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_13(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "WINDOW":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_14(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["XXwindowXX"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_15(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["WINDOW"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_16(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "XXstepXX":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_17(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "STEP":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_18(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["XXstepXX"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_19(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["STEP"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_20(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "XXmeta_uncertaintyXX": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_21(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "META_UNCERTAINTY": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_22(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["XXmeta_uncertaintyXX"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_23(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["META_UNCERTAINTY"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_24(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) >= 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_25(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 2:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_26(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = None
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_27(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"] + ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_28(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["XXaggregateXX"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_29(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["AGGREGATE"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_30(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["XXmean_cagrXX"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_31(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["MEAN_CAGR"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_32(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[2]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_33(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["XXaggregateXX"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_34(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["AGGREGATE"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_35(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["XXmean_cagrXX"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_36(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["MEAN_CAGR"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_37(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = None

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_38(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 1.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_39(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = None
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_40(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["XXaggregateXX"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_41(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["AGGREGATE"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_42(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["XXmean_cagrXX"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_43(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["MEAN_CAGR"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_44(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = None
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_45(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["XXaggregateXX"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_46(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["AGGREGATE"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_47(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["XXmean_sharpeXX"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_48(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["MEAN_SHARPE"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_49(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = None

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_50(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["XXaggregateXX"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_51(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["AGGREGATE"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_52(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["XXworst_max_drawdownXX"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_53(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["WORST_MAX_DRAWDOWN"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_54(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) != 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_55(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 1:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_56(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 1.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_57(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = None
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_58(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) * len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_59(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(None) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_60(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) * len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_61(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum(None) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_62(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) * 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_63(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v + mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_64(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 3 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_65(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = None
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_66(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(None)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_67(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = None
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_68(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(None)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_69(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = None

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_70(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(None)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_71(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = None

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_72(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance)) / (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_73(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap / (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_74(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 * (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_75(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (2.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_76(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 - cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_77(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (2.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_78(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 * (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_79(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (2.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_80(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 - sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_81(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (2.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_82(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "XXbest_paramsXX": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_83(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "BEST_PARAMS": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_84(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "XXrobustness_scoreXX": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_85(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "ROBUSTNESS_SCORE": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_86(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "XXstability_metricsXX": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_87(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "STABILITY_METRICS": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_88(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "XXtop_gapXX":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_89(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "TOP_GAP":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_90(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "XXcagr_varianceXX":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_91(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "CAGR_VARIANCE":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_92(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "XXsharpe_varianceXX":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_93(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "SHARPE_VARIANCE":   sharpe_variance,
            "drawdown_variance": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_94(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "XXdrawdown_varianceXX": drawdown_variance,
        },
    }


def x_evaluate_robustness__mutmut_95(
    selection_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate parameter robustness from run_selection() output.

    FAS COMPLIANCE:
      This function is an external layer under FAS v6.1.0. It satisfies
      all determinism guarantees (DET-01 through DET-07) and all
      prohibitions defined in ARCHITECTURE.md Section 4. Specifically:

      PROHIBITED-06 (no reimplementation):
        No metric formula from any upstream layer is reimplemented here.
        All aggregate values (mean_cagr, mean_sharpe, worst_max_drawdown)
        are consumed directly from selection_output as produced by
        run_selection(). The only computations performed here are:
        population variance (a simple aggregation), top_gap (a single
        subtraction between two already-computed values), and
        robustness_score (a deterministic formula over those aggregates).
        None of these duplicate any formula owned by a canonical layer.

      PROHIBITED-02 (no file I/O): No file is read or written.
      PROHIBITED-03 (no logging): No logging calls are made.
      PROHIBITED-05 (no global mutable state): No module-level variable
        is written to during execution.
      DET-02 (no external state reads): All inputs are passed explicitly.
      DET-03 (no side effects): selection_output is not mutated.

    INPUT CONTRACT:
      selection_output must be the direct output of run_selection().
      Expected top-level keys:
        "best_params" -- dict with "window", "step", "meta_uncertainty"
        "best_score"  -- aggregate dict (not used directly; ranking[0]
                         is the authoritative best entry)
        "ranking"     -- list of dicts, each containing:
                           "window", "step", "meta_uncertainty",
                           "aggregate" (with "mean_cagr", "mean_sharpe",
                           "worst_max_drawdown"), "score_tuple"
      ranking must be non-empty. ranking[0] is the best entry.

    COMPUTED VALUES:
      top_gap:
        mean_cagr of ranking[0] minus mean_cagr of ranking[1].
        0.0 if ranking has only one entry.

      cagr_variance:
        Population variance of mean_cagr across all ranking entries.

      sharpe_variance:
        Population variance of mean_sharpe across all ranking entries.

      drawdown_variance:
        Population variance of worst_max_drawdown across all ranking
        entries.

      robustness_score:
        top_gap * (1 / (1 + cagr_variance)) * (1 / (1 + sharpe_variance))

    Parameters
    ----------
    selection_output : dict[str, Any]
        Direct output of run_selection(). Not mutated by this function.

    Returns
    -------
    dict[str, Any]
        {
            "best_params": dict -- "window", "step", "meta_uncertainty"
                                   of the top-ranked configuration.
            "robustness_score": float -- deterministic robustness score.
            "stability_metrics": {
                "top_gap":           float,
                "cagr_variance":     float,
                "sharpe_variance":   float,
                "drawdown_variance": float,
            }
        }

    Raises
    ------
    ValueError
        If ranking is empty.
    KeyError
        If required keys are absent from selection_output or its
        nested dicts. Propagated without wrapping.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    selection_output is not mutated. All intermediate containers are
    constructed fresh per call.
    """
    ranking: list[dict] = selection_output["ranking"]

    if len(ranking) == 0:
        raise ValueError("ranking must not be empty.")

    best_entry: dict = ranking[0]
    best_params: dict = {
        "window":           best_entry["window"],
        "step":             best_entry["step"],
        "meta_uncertainty": best_entry["meta_uncertainty"],
    }

    # ------------------------------------------------------------------
    # Top gap: difference in mean_cagr between best and second best.
    # ------------------------------------------------------------------
    if len(ranking) > 1:
        top_gap: float = (
            best_entry["aggregate"]["mean_cagr"]
            - ranking[1]["aggregate"]["mean_cagr"]
        )
    else:
        top_gap = 0.0

    # ------------------------------------------------------------------
    # Collect aggregate values across all ranking entries.
    # ------------------------------------------------------------------
    cagr_values: list[float] = [
        entry["aggregate"]["mean_cagr"] for entry in ranking
    ]
    sharpe_values: list[float] = [
        entry["aggregate"]["mean_sharpe"] for entry in ranking
    ]
    drawdown_values: list[float] = [
        entry["aggregate"]["worst_max_drawdown"] for entry in ranking
    ]

    # ------------------------------------------------------------------
    # Population variance helper. Defined locally; not a reimplementation
    # of any canonical layer formula.
    # ------------------------------------------------------------------
    def _variance(values: list[float]) -> float:
        if len(values) == 0:
            return 0.0
        mean: float = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    cagr_variance: float     = _variance(cagr_values)
    sharpe_variance: float   = _variance(sharpe_values)
    drawdown_variance: float = _variance(drawdown_values)

    # ------------------------------------------------------------------
    # Robustness score.
    # ------------------------------------------------------------------
    robustness_score: float = (
        top_gap
        * (1.0 / (1.0 + cagr_variance))
        * (1.0 / (1.0 + sharpe_variance))
    )

    return {
        "best_params": best_params,
        "robustness_score": robustness_score,
        "stability_metrics": {
            "top_gap":           top_gap,
            "cagr_variance":     cagr_variance,
            "sharpe_variance":   sharpe_variance,
            "DRAWDOWN_VARIANCE": drawdown_variance,
        },
    }

x_evaluate_robustness__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_evaluate_robustness__mutmut_1': x_evaluate_robustness__mutmut_1, 
    'x_evaluate_robustness__mutmut_2': x_evaluate_robustness__mutmut_2, 
    'x_evaluate_robustness__mutmut_3': x_evaluate_robustness__mutmut_3, 
    'x_evaluate_robustness__mutmut_4': x_evaluate_robustness__mutmut_4, 
    'x_evaluate_robustness__mutmut_5': x_evaluate_robustness__mutmut_5, 
    'x_evaluate_robustness__mutmut_6': x_evaluate_robustness__mutmut_6, 
    'x_evaluate_robustness__mutmut_7': x_evaluate_robustness__mutmut_7, 
    'x_evaluate_robustness__mutmut_8': x_evaluate_robustness__mutmut_8, 
    'x_evaluate_robustness__mutmut_9': x_evaluate_robustness__mutmut_9, 
    'x_evaluate_robustness__mutmut_10': x_evaluate_robustness__mutmut_10, 
    'x_evaluate_robustness__mutmut_11': x_evaluate_robustness__mutmut_11, 
    'x_evaluate_robustness__mutmut_12': x_evaluate_robustness__mutmut_12, 
    'x_evaluate_robustness__mutmut_13': x_evaluate_robustness__mutmut_13, 
    'x_evaluate_robustness__mutmut_14': x_evaluate_robustness__mutmut_14, 
    'x_evaluate_robustness__mutmut_15': x_evaluate_robustness__mutmut_15, 
    'x_evaluate_robustness__mutmut_16': x_evaluate_robustness__mutmut_16, 
    'x_evaluate_robustness__mutmut_17': x_evaluate_robustness__mutmut_17, 
    'x_evaluate_robustness__mutmut_18': x_evaluate_robustness__mutmut_18, 
    'x_evaluate_robustness__mutmut_19': x_evaluate_robustness__mutmut_19, 
    'x_evaluate_robustness__mutmut_20': x_evaluate_robustness__mutmut_20, 
    'x_evaluate_robustness__mutmut_21': x_evaluate_robustness__mutmut_21, 
    'x_evaluate_robustness__mutmut_22': x_evaluate_robustness__mutmut_22, 
    'x_evaluate_robustness__mutmut_23': x_evaluate_robustness__mutmut_23, 
    'x_evaluate_robustness__mutmut_24': x_evaluate_robustness__mutmut_24, 
    'x_evaluate_robustness__mutmut_25': x_evaluate_robustness__mutmut_25, 
    'x_evaluate_robustness__mutmut_26': x_evaluate_robustness__mutmut_26, 
    'x_evaluate_robustness__mutmut_27': x_evaluate_robustness__mutmut_27, 
    'x_evaluate_robustness__mutmut_28': x_evaluate_robustness__mutmut_28, 
    'x_evaluate_robustness__mutmut_29': x_evaluate_robustness__mutmut_29, 
    'x_evaluate_robustness__mutmut_30': x_evaluate_robustness__mutmut_30, 
    'x_evaluate_robustness__mutmut_31': x_evaluate_robustness__mutmut_31, 
    'x_evaluate_robustness__mutmut_32': x_evaluate_robustness__mutmut_32, 
    'x_evaluate_robustness__mutmut_33': x_evaluate_robustness__mutmut_33, 
    'x_evaluate_robustness__mutmut_34': x_evaluate_robustness__mutmut_34, 
    'x_evaluate_robustness__mutmut_35': x_evaluate_robustness__mutmut_35, 
    'x_evaluate_robustness__mutmut_36': x_evaluate_robustness__mutmut_36, 
    'x_evaluate_robustness__mutmut_37': x_evaluate_robustness__mutmut_37, 
    'x_evaluate_robustness__mutmut_38': x_evaluate_robustness__mutmut_38, 
    'x_evaluate_robustness__mutmut_39': x_evaluate_robustness__mutmut_39, 
    'x_evaluate_robustness__mutmut_40': x_evaluate_robustness__mutmut_40, 
    'x_evaluate_robustness__mutmut_41': x_evaluate_robustness__mutmut_41, 
    'x_evaluate_robustness__mutmut_42': x_evaluate_robustness__mutmut_42, 
    'x_evaluate_robustness__mutmut_43': x_evaluate_robustness__mutmut_43, 
    'x_evaluate_robustness__mutmut_44': x_evaluate_robustness__mutmut_44, 
    'x_evaluate_robustness__mutmut_45': x_evaluate_robustness__mutmut_45, 
    'x_evaluate_robustness__mutmut_46': x_evaluate_robustness__mutmut_46, 
    'x_evaluate_robustness__mutmut_47': x_evaluate_robustness__mutmut_47, 
    'x_evaluate_robustness__mutmut_48': x_evaluate_robustness__mutmut_48, 
    'x_evaluate_robustness__mutmut_49': x_evaluate_robustness__mutmut_49, 
    'x_evaluate_robustness__mutmut_50': x_evaluate_robustness__mutmut_50, 
    'x_evaluate_robustness__mutmut_51': x_evaluate_robustness__mutmut_51, 
    'x_evaluate_robustness__mutmut_52': x_evaluate_robustness__mutmut_52, 
    'x_evaluate_robustness__mutmut_53': x_evaluate_robustness__mutmut_53, 
    'x_evaluate_robustness__mutmut_54': x_evaluate_robustness__mutmut_54, 
    'x_evaluate_robustness__mutmut_55': x_evaluate_robustness__mutmut_55, 
    'x_evaluate_robustness__mutmut_56': x_evaluate_robustness__mutmut_56, 
    'x_evaluate_robustness__mutmut_57': x_evaluate_robustness__mutmut_57, 
    'x_evaluate_robustness__mutmut_58': x_evaluate_robustness__mutmut_58, 
    'x_evaluate_robustness__mutmut_59': x_evaluate_robustness__mutmut_59, 
    'x_evaluate_robustness__mutmut_60': x_evaluate_robustness__mutmut_60, 
    'x_evaluate_robustness__mutmut_61': x_evaluate_robustness__mutmut_61, 
    'x_evaluate_robustness__mutmut_62': x_evaluate_robustness__mutmut_62, 
    'x_evaluate_robustness__mutmut_63': x_evaluate_robustness__mutmut_63, 
    'x_evaluate_robustness__mutmut_64': x_evaluate_robustness__mutmut_64, 
    'x_evaluate_robustness__mutmut_65': x_evaluate_robustness__mutmut_65, 
    'x_evaluate_robustness__mutmut_66': x_evaluate_robustness__mutmut_66, 
    'x_evaluate_robustness__mutmut_67': x_evaluate_robustness__mutmut_67, 
    'x_evaluate_robustness__mutmut_68': x_evaluate_robustness__mutmut_68, 
    'x_evaluate_robustness__mutmut_69': x_evaluate_robustness__mutmut_69, 
    'x_evaluate_robustness__mutmut_70': x_evaluate_robustness__mutmut_70, 
    'x_evaluate_robustness__mutmut_71': x_evaluate_robustness__mutmut_71, 
    'x_evaluate_robustness__mutmut_72': x_evaluate_robustness__mutmut_72, 
    'x_evaluate_robustness__mutmut_73': x_evaluate_robustness__mutmut_73, 
    'x_evaluate_robustness__mutmut_74': x_evaluate_robustness__mutmut_74, 
    'x_evaluate_robustness__mutmut_75': x_evaluate_robustness__mutmut_75, 
    'x_evaluate_robustness__mutmut_76': x_evaluate_robustness__mutmut_76, 
    'x_evaluate_robustness__mutmut_77': x_evaluate_robustness__mutmut_77, 
    'x_evaluate_robustness__mutmut_78': x_evaluate_robustness__mutmut_78, 
    'x_evaluate_robustness__mutmut_79': x_evaluate_robustness__mutmut_79, 
    'x_evaluate_robustness__mutmut_80': x_evaluate_robustness__mutmut_80, 
    'x_evaluate_robustness__mutmut_81': x_evaluate_robustness__mutmut_81, 
    'x_evaluate_robustness__mutmut_82': x_evaluate_robustness__mutmut_82, 
    'x_evaluate_robustness__mutmut_83': x_evaluate_robustness__mutmut_83, 
    'x_evaluate_robustness__mutmut_84': x_evaluate_robustness__mutmut_84, 
    'x_evaluate_robustness__mutmut_85': x_evaluate_robustness__mutmut_85, 
    'x_evaluate_robustness__mutmut_86': x_evaluate_robustness__mutmut_86, 
    'x_evaluate_robustness__mutmut_87': x_evaluate_robustness__mutmut_87, 
    'x_evaluate_robustness__mutmut_88': x_evaluate_robustness__mutmut_88, 
    'x_evaluate_robustness__mutmut_89': x_evaluate_robustness__mutmut_89, 
    'x_evaluate_robustness__mutmut_90': x_evaluate_robustness__mutmut_90, 
    'x_evaluate_robustness__mutmut_91': x_evaluate_robustness__mutmut_91, 
    'x_evaluate_robustness__mutmut_92': x_evaluate_robustness__mutmut_92, 
    'x_evaluate_robustness__mutmut_93': x_evaluate_robustness__mutmut_93, 
    'x_evaluate_robustness__mutmut_94': x_evaluate_robustness__mutmut_94, 
    'x_evaluate_robustness__mutmut_95': x_evaluate_robustness__mutmut_95
}
x_evaluate_robustness__mutmut_orig.__name__ = 'x_evaluate_robustness'
