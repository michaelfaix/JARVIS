# jarvis/report/engine.py
# Version: 1.1.0
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
#   Assembles structured reports by delegating metric computation
#   entirely to compute_metrics(), regime_conditional_returns(),
#   and TrustScoreEngine.compute(). No metric logic is reimplemented here.
#
# Standard import pattern:
#   from jarvis.report.engine import generate_report, generate_enriched_report

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from jarvis.metrics import compute_metrics, regime_conditional_returns
from jarvis.metrics.trust_score import TrustScoreEngine, TrustScoreResult
from jarvis.simulation.strategy_lab import StressTestResult


def generate_report(
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


# =============================================================================
# ENRICHED REPORT -- structured frozen dataclass output
# =============================================================================

@dataclass(frozen=True)
class ReportResult:
    """Structured enriched report aggregating all analysis outputs.

    Attributes:
        equity_curve:       Portfolio equity values (as tuple for immutability).
        metrics:            Core metrics from compute_metrics().
        regime_returns:     Regime-conditional return statistics (optional).
        stress_results:     Stress test results (optional, as tuple).
        trust_score:        TrustScoreEngine output (optional).
        periods_per_year:   Annualization factor used.
    """
    equity_curve:     Tuple[float, ...]
    metrics:          Dict[str, float]
    regime_returns:   Optional[Dict[str, Dict[str, float]]]
    stress_results:   Optional[Tuple[StressTestResult, ...]]
    trust_score:      Optional[TrustScoreResult]
    periods_per_year: int


def generate_enriched_report(
    equity_curve: List[float],
    *,
    periods_per_year: int = 252,
    returns: Optional[List[float]] = None,
    regime_labels: Optional[List[str]] = None,
    stress_results: Optional[Sequence[StressTestResult]] = None,
    trust_ece: Optional[float] = None,
    trust_ood_recall: Optional[float] = None,
    trust_prediction_variance: Optional[float] = None,
    trust_drawdown: Optional[float] = None,
    trust_uptime: Optional[float] = None,
) -> ReportResult:
    """
    Generate an enriched performance report aggregating multiple analysis
    sources into a single structured ReportResult.

    Delegates all computation to canonical owners:
      - compute_metrics() for core performance metrics (PROHIBITED-06).
      - regime_conditional_returns() for regime-conditional analysis.
      - TrustScoreEngine.compute() for trust score evaluation.

    Optional sections are included only when their inputs are provided.
    When omitted, corresponding fields are None (backward compatible).

    Parameters
    ----------
    equity_curve : List[float]
        Portfolio equity values. Must contain >= 2 values, all > 0.
    periods_per_year : int
        Annualization factor (default 252).
    returns : Optional[List[float]]
        Per-period returns for regime-conditional analysis.
        Required together with regime_labels.
    regime_labels : Optional[List[str]]
        Regime label per period (e.g., "RISK_ON", "CRISIS").
        Required together with returns. Length must match returns.
    stress_results : Optional[Sequence[StressTestResult]]
        Pre-computed stress test results to include in the report.
    trust_ece : Optional[float]
        Expected Calibration Error for TrustScoreEngine.
        All five trust_* parameters must be provided together.
    trust_ood_recall : Optional[float]
        OOD detection recall [0, 1].
    trust_prediction_variance : Optional[float]
        Prediction variance [0, inf).
    trust_drawdown : Optional[float]
        Max drawdown [0, 1].
    trust_uptime : Optional[float]
        System uptime fraction [0, 1].

    Returns
    -------
    ReportResult
        Frozen dataclass with all analysis results.

    Raises
    ------
    ValueError
        If equity_curve has < 2 values.
        If returns and regime_labels have mismatched lengths.
        If only one of returns/regime_labels is provided.
        If trust_* parameters are partially provided.
    """
    if len(equity_curve) < 2:
        raise ValueError(
            f"equity_curve must contain at least 2 values. "
            f"Received: {len(equity_curve)}"
        )

    # 1. Core metrics (delegated to compute_metrics)
    metrics: Dict[str, float] = compute_metrics(
        equity_curve=equity_curve,
        periods_per_year=periods_per_year,
    )

    # 2. Regime-conditional returns (optional)
    regime_returns: Optional[Dict[str, Dict[str, float]]] = None
    if returns is not None and regime_labels is not None:
        regime_returns = regime_conditional_returns(
            returns=returns,
            regime_labels=regime_labels,
        )
    elif (returns is None) != (regime_labels is None):
        raise ValueError(
            "returns and regime_labels must both be provided or both omitted."
        )

    # 3. Stress test results (optional, convert to tuple)
    stress_tuple: Optional[Tuple[StressTestResult, ...]] = None
    if stress_results is not None:
        stress_tuple = tuple(stress_results)

    # 4. Trust score (optional, all five params required together)
    trust_result: Optional[TrustScoreResult] = None
    trust_params = (
        trust_ece, trust_ood_recall, trust_prediction_variance,
        trust_drawdown, trust_uptime,
    )
    trust_provided = [p is not None for p in trust_params]

    if all(trust_provided):
        engine = TrustScoreEngine()
        trust_result = engine.compute(
            ece=trust_ece,
            ood_recall=trust_ood_recall,
            prediction_variance=trust_prediction_variance,
            drawdown=trust_drawdown,
            uptime=trust_uptime,
        )
    elif any(trust_provided):
        raise ValueError(
            "All five trust_* parameters must be provided together "
            "(trust_ece, trust_ood_recall, trust_prediction_variance, "
            "trust_drawdown, trust_uptime), or all omitted."
        )

    return ReportResult(
        equity_curve=tuple(equity_curve),
        metrics=metrics,
        regime_returns=regime_returns,
        stress_results=stress_tuple,
        trust_score=trust_result,
        periods_per_year=periods_per_year,
    )


__all__ = ["generate_report", "generate_enriched_report", "ReportResult"]
