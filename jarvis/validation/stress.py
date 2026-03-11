# =============================================================================
# jarvis/validation/stress.py — S15 Stress Test Framework
#
# Authority: FAS v6.0.1, S15
#
# 5 categories x 3 severities = 15 stress scenarios for system certification.
#
# Categories: VOLATILITY, CORRELATION, LIQUIDITY, REGIME, DATA_LOSS
# Severities: LOW, MEDIUM, HIGH
#
# Entry points:
#   generate_stress_scenarios()    -> tuple of StressScenario
#   run_stress_scenario()          -> StressResult
#   run_stress_certification()     -> tuple of StressResult
#   get_certification_summary()    -> dict
#
# CLASSIFICATION: Tier 6 — ANALYSIS AND STRATEGY RESEARCH TOOL.
#
# DETERMINISM CONSTRAINTS
# -----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-04  Deterministic arithmetic only.
# DET-05  All branching is deterministic.
# DET-06  Fixed literals are not parametrised.
# DET-07  Same inputs = bit-identical outputs.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT
# ------------------------------------
#   No numpy / scipy / sklearn / torch
#   No logging module
#   No datetime.now() / time.time()
#   No random / secrets / uuid
#   No file IO / network IO
#   No global mutable state
#
# DEPENDENCIES
# ------------
#   stdlib:   dataclasses, math
#   internal: NONE
#   external: NONE (pure Python)
# =============================================================================

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    "StressScenario",
    "StressResult",
    "STRESS_CATEGORIES",
    "SEVERITY_LEVELS",
    "generate_stress_scenarios",
    "run_stress_scenario",
    "run_stress_certification",
    "get_certification_summary",
]


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals, not parametrisable)
# =============================================================================

STRESS_CATEGORIES: tuple = (
    "VOLATILITY",
    "CORRELATION",
    "LIQUIDITY",
    "REGIME",
    "DATA_LOSS",
)
"""5 stress test categories."""

SEVERITY_LEVELS: tuple = ("LOW", "MEDIUM", "HIGH")
"""3 severity levels per category."""

# Scenario parameter definitions (DET-06: fixed)
_SCENARIO_PARAMS: dict = {
    ("VOLATILITY", "LOW"): {
        "multiplier": 2.0,
        "description": "Volatility at 2x baseline",
    },
    ("VOLATILITY", "MEDIUM"): {
        "multiplier": 5.0,
        "description": "Volatility at 5x baseline",
    },
    ("VOLATILITY", "HIGH"): {
        "multiplier": 10.0,
        "description": "Volatility at 10x baseline",
    },
    ("CORRELATION", "LOW"): {
        "avg_correlation": 0.5,
        "description": "Average correlation 0.5",
    },
    ("CORRELATION", "MEDIUM"): {
        "avg_correlation": 0.8,
        "description": "Average correlation 0.8",
    },
    ("CORRELATION", "HIGH"): {
        "avg_correlation": 0.95,
        "description": "Average correlation 0.95",
    },
    ("LIQUIDITY", "LOW"): {
        "reduction": 0.50,
        "description": "50% liquidity reduction",
    },
    ("LIQUIDITY", "MEDIUM"): {
        "reduction": 0.80,
        "description": "80% liquidity reduction",
    },
    ("LIQUIDITY", "HIGH"): {
        "reduction": 0.95,
        "description": "95% liquidity reduction",
    },
    ("REGIME", "LOW"): {
        "n_changes": 2,
        "description": "2 regime changes",
    },
    ("REGIME", "MEDIUM"): {
        "n_changes": 5,
        "description": "5 regime changes",
    },
    ("REGIME", "HIGH"): {
        "n_changes": 10,
        "description": "10 regime changes",
    },
    ("DATA_LOSS", "LOW"): {
        "missing_fraction": 0.10,
        "description": "10% missing data",
    },
    ("DATA_LOSS", "MEDIUM"): {
        "missing_fraction": 0.30,
        "description": "30% missing data",
    },
    ("DATA_LOSS", "HIGH"): {
        "missing_fraction": 0.50,
        "description": "50% missing data",
    },
}

# Severity degradation factors (DET-06: fixed)
_SEVERITY_DEGRADATION: dict = {
    "LOW": 0.85,
    "MEDIUM": 0.60,
    "HIGH": 0.35,
}
"""Expected quality retention factor per severity level."""

# Pass threshold for a stress test
_PASS_THRESHOLD: float = 0.5
"""Score must be >= 0.5 to pass (system maintains 50% effectiveness)."""


# =============================================================================
# SECTION 2 -- DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class StressScenario:
    """A single stress test scenario."""
    category: str
    severity: str
    description: str
    parameters: dict

    def __post_init__(self) -> None:
        if not isinstance(self.category, str):
            raise TypeError(
                f"StressScenario.category must be str, "
                f"got {type(self.category).__name__}"
            )
        if not isinstance(self.severity, str):
            raise TypeError(
                f"StressScenario.severity must be str, "
                f"got {type(self.severity).__name__}"
            )
        if not isinstance(self.description, str):
            raise TypeError(
                f"StressScenario.description must be str, "
                f"got {type(self.description).__name__}"
            )
        if not isinstance(self.parameters, dict):
            raise TypeError(
                f"StressScenario.parameters must be dict, "
                f"got {type(self.parameters).__name__}"
            )


@dataclass(frozen=True)
class StressResult:
    """Result of a stress test."""
    scenario: StressScenario
    passed: bool
    score: float
    details: str

    def __post_init__(self) -> None:
        if not isinstance(self.scenario, StressScenario):
            raise TypeError(
                f"StressResult.scenario must be StressScenario, "
                f"got {type(self.scenario).__name__}"
            )
        if not isinstance(self.passed, bool):
            raise TypeError(
                f"StressResult.passed must be bool, "
                f"got {type(self.passed).__name__}"
            )
        if not isinstance(self.score, (int, float)):
            raise TypeError(
                f"StressResult.score must be numeric, "
                f"got {type(self.score).__name__}"
            )
        if not math.isfinite(self.score):
            raise ValueError(
                f"StressResult.score must be finite, got {self.score!r}"
            )
        if not isinstance(self.details, str):
            raise TypeError(
                f"StressResult.details must be str, "
                f"got {type(self.details).__name__}"
            )


# =============================================================================
# SECTION 3 -- GENERATE STRESS SCENARIOS
# =============================================================================

def generate_stress_scenarios() -> tuple:
    """
    Generate all 15 stress scenarios (5 categories x 3 severities).

    Returns:
        Tuple of 15 StressScenario objects in deterministic order.
    """
    scenarios = []
    for category in STRESS_CATEGORIES:
        for severity in SEVERITY_LEVELS:
            params = _SCENARIO_PARAMS[(category, severity)]
            scenarios.append(StressScenario(
                category=category,
                severity=severity,
                description=params["description"],
                parameters={
                    k: v for k, v in params.items() if k != "description"
                },
            ))
    return tuple(scenarios)


# =============================================================================
# SECTION 4 -- RUN STRESS SCENARIO
# =============================================================================

def _compute_stress_score(
    scenario: StressScenario,
    baseline_metrics: dict,
) -> float:
    """
    Compute how well the system maintains quality under stress.

    Score = baseline_quality * severity_degradation_factor * category_modifier

    The score is in [0, 1]. Higher is better.
    """
    # Extract baseline quality (default to 1.0 if not provided)
    baseline_quality = baseline_metrics.get("quality", 1.0)
    if not isinstance(baseline_quality, (int, float)) or not math.isfinite(baseline_quality):
        baseline_quality = 0.5

    baseline_quality = max(0.0, min(1.0, baseline_quality))

    # Get severity degradation factor
    degradation = _SEVERITY_DEGRADATION.get(scenario.severity, 0.5)

    # Category-specific modifiers based on baseline metrics
    category = scenario.category
    modifier = 1.0

    if category == "VOLATILITY":
        # Higher baseline vol_resilience helps
        vol_resilience = baseline_metrics.get("vol_resilience", 0.5)
        if isinstance(vol_resilience, (int, float)) and math.isfinite(vol_resilience):
            modifier = max(0.1, min(1.0, vol_resilience))

    elif category == "CORRELATION":
        # Diversification helps against correlation stress
        diversification = baseline_metrics.get("diversification", 0.5)
        if isinstance(diversification, (int, float)) and math.isfinite(diversification):
            modifier = max(0.1, min(1.0, diversification))

    elif category == "LIQUIDITY":
        # Liquidity buffer helps
        liquidity_buffer = baseline_metrics.get("liquidity_buffer", 0.5)
        if isinstance(liquidity_buffer, (int, float)) and math.isfinite(liquidity_buffer):
            modifier = max(0.1, min(1.0, liquidity_buffer))

    elif category == "REGIME":
        # Regime detection quality helps
        regime_detection = baseline_metrics.get("regime_detection", 0.5)
        if isinstance(regime_detection, (int, float)) and math.isfinite(regime_detection):
            modifier = max(0.1, min(1.0, regime_detection))

    elif category == "DATA_LOSS":
        # Data completeness baseline
        data_completeness = baseline_metrics.get("data_completeness", 0.5)
        if isinstance(data_completeness, (int, float)) and math.isfinite(data_completeness):
            modifier = max(0.1, min(1.0, data_completeness))

    score = baseline_quality * degradation * modifier
    score = max(0.0, min(1.0, score))

    if not math.isfinite(score):
        score = 0.0

    return score


def run_stress_scenario(
    scenario: StressScenario,
    baseline_metrics: dict,
) -> StressResult:
    """
    Run a single stress scenario against baseline metrics.
    Score = how well the system maintains quality under stress.
    passed = score >= 0.5 (system maintains at least 50% effectiveness).
    """
    if not isinstance(scenario, StressScenario):
        raise TypeError(
            f"scenario must be StressScenario, "
            f"got {type(scenario).__name__}"
        )
    if not isinstance(baseline_metrics, dict):
        raise TypeError(
            f"baseline_metrics must be dict, "
            f"got {type(baseline_metrics).__name__}"
        )

    score = _compute_stress_score(scenario, baseline_metrics)
    passed = score >= _PASS_THRESHOLD

    return StressResult(
        scenario=scenario,
        passed=passed,
        score=score,
        details=(
            f"{scenario.category}/{scenario.severity}: "
            f"score={score:.3f}, "
            f"{'PASS' if passed else 'FAIL'}"
        ),
    )


# =============================================================================
# SECTION 5 -- RUN STRESS CERTIFICATION
# =============================================================================

def run_stress_certification(baseline_metrics: dict) -> tuple:
    """Run all 15 stress scenarios, return tuple of StressResult."""
    if not isinstance(baseline_metrics, dict):
        raise TypeError(
            f"baseline_metrics must be dict, "
            f"got {type(baseline_metrics).__name__}"
        )

    scenarios = generate_stress_scenarios()
    results = []
    for scenario in scenarios:
        result = run_stress_scenario(scenario, baseline_metrics)
        results.append(result)
    return tuple(results)


# =============================================================================
# SECTION 6 -- CERTIFICATION SUMMARY
# =============================================================================

def get_certification_summary(results: tuple) -> dict:
    """
    Summarize stress certification.
    Returns {total, passed, failed, pass_rate, by_category, by_severity}.
    """
    if not isinstance(results, tuple):
        raise TypeError(
            f"results must be tuple, got {type(results).__name__}"
        )

    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    pass_rate = passed / total if total > 0 else 0.0

    # By category
    by_category = {}
    for cat in STRESS_CATEGORIES:
        cat_results = [r for r in results if r.scenario.category == cat]
        cat_total = len(cat_results)
        cat_passed = sum(1 for r in cat_results if r.passed)
        by_category[cat] = {
            "total": cat_total,
            "passed": cat_passed,
            "failed": cat_total - cat_passed,
            "pass_rate": cat_passed / cat_total if cat_total > 0 else 0.0,
        }

    # By severity
    by_severity = {}
    for sev in SEVERITY_LEVELS:
        sev_results = [r for r in results if r.scenario.severity == sev]
        sev_total = len(sev_results)
        sev_passed = sum(1 for r in sev_results if r.passed)
        by_severity[sev] = {
            "total": sev_total,
            "passed": sev_passed,
            "failed": sev_total - sev_passed,
            "pass_rate": sev_passed / sev_total if sev_total > 0 else 0.0,
        }

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": pass_rate,
        "by_category": by_category,
        "by_severity": by_severity,
    }
