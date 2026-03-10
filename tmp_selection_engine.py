# =============================================================================
# JARVIS v6.1.0 -- SELECTION ENGINE
# File:   jarvis/selection/engine.py
# Version: 1.2.0
# =============================================================================
#
# SCOPE
# -----
# Deterministic instrument/parameter selection engine. Ranks candidates by
# a caller-supplied score function and applies configurable filters.
# run_selection() consumes run_optimization() output, scores each parameter
# combination by a deterministic multi-criteria ranking, and produces a
# structured result consumed by evaluate_robustness().
#
# PUBLIC FUNCTIONS
# ----------------
#   rank_candidates(candidates, score_fn, descending) -> List[str]
#   filter_by_threshold(candidates, scores, threshold) -> List[str]
#   select_top_n(candidates, scores, n) -> List[str]
#   run_selection(optimization_output, top_n, min_sharpe) -> dict
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
# =============================================================================

from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Sequence, Tuple


# ---------------------------------------------------------------------------
# RANK CANDIDATES
# ---------------------------------------------------------------------------

def rank_candidates(
    candidates:  Sequence[str],
    score_fn:    Callable[[str], float],
    descending:  bool = True,
) -> List[str]:
    """
    Rank instrument symbols by a deterministic score function.

    Ties are broken lexicographically (ascending symbol name) to ensure
    deterministic output regardless of input order.

    Args:
        candidates:  Sequence of instrument symbol strings.
        score_fn:    Pure function mapping symbol -> float score.
        descending:  If True, highest score ranked first (default: True).

    Returns:
        List of symbols sorted by score, then by symbol for tie-breaking.
    """
    scored = [(score_fn(sym), sym) for sym in candidates]
    scored.sort(key=lambda x: (-x[0] if descending else x[0], x[1]))
    return [sym for _, sym in scored]


# ---------------------------------------------------------------------------
# FILTER BY THRESHOLD
# ---------------------------------------------------------------------------

def filter_by_threshold(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    threshold:   float,
) -> List[str]:
    """
    Filter candidates to those whose score >= threshold.

    Returns list sorted by descending score, then ascending symbol (deterministic).

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Symbols not in scores receive 0.0.
        threshold:   Minimum score (inclusive).

    Returns:
        Filtered and sorted list of symbols.
    """
    qualified = [
        (scores.get(sym, 0.0), sym)
        for sym in candidates
        if scores.get(sym, 0.0) >= threshold
    ]
    qualified.sort(key=lambda x: (-x[0], x[1]))
    return [sym for _, sym in qualified]


# ---------------------------------------------------------------------------
# SELECT TOP N
# ---------------------------------------------------------------------------

def select_top_n(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    n:           int,
) -> List[str]:
    """
    Select top-n candidates by score.

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Missing symbols scored 0.0.
        n:           Number of candidates to select. If n >= len(candidates),
                     all candidates are returned (sorted).

    Returns:
        List of up to n symbols, sorted by descending score then ascending symbol.

    Raises:
        ValueError if n < 0.
    """
    if n < 0:
        raise ValueError(f"n must be >= 0; got {n}")
    ranked = filter_by_threshold(candidates, scores, threshold=float('-inf'))
    return ranked[:n]


# ---------------------------------------------------------------------------
# SCORING HELPERS (internal)
# ---------------------------------------------------------------------------

def _safe_cagr(aggregate: dict) -> float:
    """Extract CAGR from aggregate metrics, defaulting to 0.0."""
    return float(aggregate.get("cagr", 0.0))


def _safe_sharpe(aggregate: dict) -> float:
    """Extract Sharpe ratio from aggregate metrics, defaulting to 0.0."""
    return float(aggregate.get("sharpe_ratio", 0.0))


def _safe_max_drawdown(aggregate: dict) -> float:
    """Extract max drawdown from aggregate metrics, defaulting to 1.0."""
    return float(aggregate.get("max_drawdown", 1.0))


def _compute_score_tuple(aggregate: dict) -> Tuple[float, float, float]:
    """
    Compute a deterministic multi-criteria score tuple from aggregate metrics.

    Score tuple ordering: (sharpe_ratio, cagr, -max_drawdown).
    Higher is better for all three components.
    Sorting this tuple lexicographically (descending) ranks configurations
    by Sharpe first, then CAGR, then least drawdown.
    """
    sharpe = _safe_sharpe(aggregate)
    cagr = _safe_cagr(aggregate)
    mdd = _safe_max_drawdown(aggregate)
    return (sharpe, cagr, -mdd)


# ---------------------------------------------------------------------------
# RUN SELECTION
# ---------------------------------------------------------------------------

def run_selection(
    optimization_output: list[dict],
    top_n:               int = 10,
    min_sharpe:          float = float('-inf'),
) -> dict[str, Any]:
    """
    Select and rank parameter configurations from run_optimization() output.

    Consumes the output of jarvis.optimization.run_optimization() and
    produces a ranked list of parameter configurations scored by a
    deterministic multi-criteria ranking. The output structure is
    consumed by jarvis.robustness.evaluate_robustness().

    SCORING:
        Each configuration is scored by a tuple:
            (sharpe_ratio, cagr, -max_drawdown)
        sorted lexicographically in descending order. Ties are broken
        deterministically by (window ASC, step ASC, meta_uncertainty ASC).

    FILTERING:
        Configurations whose aggregate Sharpe ratio is below min_sharpe
        are excluded from ranking before top_n selection.

    AGGREGATE ENRICHMENT:
        Each ranking entry's aggregate dict is enriched with:
            "mean_cagr"            -- same as cagr (single-asset view)
            "mean_sharpe"          -- same as sharpe_ratio
            "worst_max_drawdown"   -- same as max_drawdown
        These keys are required by evaluate_robustness().

    Parameters
    ----------
    optimization_output : list[dict]
        Direct output of run_optimization(). Each entry has keys:
            "window", "step", "meta_uncertainty", "result".
        "result" contains "aggregate" dict with metric keys.
        Not mutated by this function.
    top_n : int
        Maximum number of configurations to include in ranking.
        Must be >= 1. Default 10.
    min_sharpe : float
        Minimum Sharpe ratio for inclusion. Default -inf (no filter).

    Returns
    -------
    dict with keys:
        "best_params"  -- dict with "window", "step", "meta_uncertainty"
                          of the top-ranked configuration.
                          Empty dict if no configurations qualify.
        "best_score"   -- aggregate dict of best configuration,
                          or empty dict if none qualify.
        "ranking"      -- list of up to top_n dicts, each containing:
                            "window", "step", "meta_uncertainty",
                            "aggregate" (enriched), "score_tuple".
                          Sorted descending by score_tuple, then by
                          (window, step, meta_uncertainty) for ties.

    Raises
    ------
    ValueError
        If top_n < 1.
        If optimization_output is empty.
    """
    if top_n < 1:
        raise ValueError(f"top_n must be >= 1; got {top_n}")
    if not optimization_output:
        raise ValueError("optimization_output must not be empty.")

    # ------------------------------------------------------------------
    # Score and filter each configuration.
    # ------------------------------------------------------------------
    scored: list[dict] = []

    for entry in optimization_output:
        window: int = entry["window"]
        step: int = entry["step"]
        meta_uncertainty: float = entry["meta_uncertainty"]
        aggregate: dict = entry["result"].get("aggregate", {})

        sharpe = _safe_sharpe(aggregate)
        if sharpe < min_sharpe:
            continue

        score_tuple = _compute_score_tuple(aggregate)

        enriched_aggregate: dict = dict(aggregate)
        enriched_aggregate["mean_cagr"] = _safe_cagr(aggregate)
        enriched_aggregate["mean_sharpe"] = _safe_sharpe(aggregate)
        enriched_aggregate["worst_max_drawdown"] = _safe_max_drawdown(aggregate)

        scored.append({
            "window": window,
            "step": step,
            "meta_uncertainty": meta_uncertainty,
            "aggregate": enriched_aggregate,
            "score_tuple": score_tuple,
        })

    # ------------------------------------------------------------------
    # Deterministic sort: descending by score_tuple, then ascending by
    # (window, step, meta_uncertainty) for tie-breaking.
    # ------------------------------------------------------------------
    scored.sort(
        key=lambda x: (
            (-x["score_tuple"][0], -x["score_tuple"][1], -x["score_tuple"][2]),
            x["window"],
            x["step"],
            x["meta_uncertainty"],
        )
    )

    # ------------------------------------------------------------------
    # Select top N.
    # ------------------------------------------------------------------
    ranking: list[dict] = scored[:top_n]

    # ------------------------------------------------------------------
    # Build output.
    # ------------------------------------------------------------------
    if ranking:
        best = ranking[0]
        best_params: dict = {
            "window": best["window"],
            "step": best["step"],
            "meta_uncertainty": best["meta_uncertainty"],
        }
        best_score: dict = best["aggregate"]
    else:
        best_params = {}
        best_score = {}

    return {
        "best_params": best_params,
        "best_score": best_score,
        "ranking": ranking,
    }


__all__ = [
    "rank_candidates",
    "filter_by_threshold",
    "select_top_n",
    "run_selection",
]
