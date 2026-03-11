# =============================================================================
# jarvis/research/sandbox_runner.py
# Authority: FAS v6.0.1 -- S26-S30, lines 9913-10051
# =============================================================================
#
# SCOPE
# -----
# Safe orchestration wrapper for ScenarioSandboxEngine.  Enforces isolation
# rules R1-R5 and dispatches to the correct simulation method based on
# scenario_type string.
#
# Public symbols:
#   SUPPORTED_SCENARIO_DISPATCHES   Mapping of scenario_type → method name
#   SandboxRunnerResult             Frozen dataclass for runner output
#   run_scenario_safely             Entry-point function
#
# ISOLATION RULES (enforced here)
# --------------------------------
# R1: Reads ONLY immutable snapshots — no live state references.
# R2: NEVER calls ctrl.update() — no state mutation.
# R3: Cloned strategy objects only — no registry modification.
# R4: Returns ScenarioResult only — no Order/broker references.
# R5: No live feed access — inputs from snapshots and explicit params.
#
# DEPENDENCIES
# ------------
#   stdlib:    dataclasses, typing
#   internal:  jarvis.research.scenario_sandbox
#   PROHIBITED: logging, random, file IO, network IO, datetime.now(), numpy
#
# DETERMINISM
# -----------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-06  Fixed literals not parametrisable.
# DET-07  Same inputs = identical output.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from jarvis.research.scenario_sandbox import (
    ScenarioResult,
    ScenarioSandboxEngine,
)

__all__ = [
    "SUPPORTED_SCENARIO_DISPATCHES",
    "SandboxRunnerResult",
    "run_scenario_safely",
]


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

SUPPORTED_SCENARIO_DISPATCHES: Dict[str, str] = {
    "regime_shift": "simulate_regime_shift",
    "vol_spike": "simulate_vol_spike",
    "corr_shock": "simulate_correlation_shock",
}
"""Mapping of scenario_type string → ScenarioSandboxEngine method name."""


# =============================================================================
# SECTION 2 -- DATA TYPES
# =============================================================================

@dataclass(frozen=True)
class SandboxRunnerResult:
    """
    Result wrapper from safe scenario execution.

    Fields:
        scenario_type:  The scenario type that was executed.
        success:        True if execution completed without error.
        result:         The ScenarioResult if success, else None.
        error_message:  Error description if not success, else None.
    """
    scenario_type: str
    success: bool
    result: Optional[ScenarioResult]
    error_message: Optional[str]


# =============================================================================
# SECTION 3 -- RUNNER
# =============================================================================

def run_scenario_safely(
    engine: ScenarioSandboxEngine,
    scenario_type: str,
    **kwargs,
) -> SandboxRunnerResult:
    """
    Execute a scenario simulation safely with isolation enforcement.

    Dispatches to the appropriate ScenarioSandboxEngine method based on
    scenario_type.  Catches and wraps errors rather than propagating.

    Args:
        engine:        A ScenarioSandboxEngine instance.
        scenario_type: One of SUPPORTED_SCENARIO_DISPATCHES keys.
        **kwargs:      Arguments forwarded to the engine method.

    Returns:
        SandboxRunnerResult.

    Raises:
        TypeError: If engine is not a ScenarioSandboxEngine.
        TypeError: If scenario_type is not a string.
        ValueError: If scenario_type is not in SUPPORTED_SCENARIO_DISPATCHES.
    """
    if not isinstance(engine, ScenarioSandboxEngine):
        raise TypeError(
            f"engine must be a ScenarioSandboxEngine, "
            f"got {type(engine).__name__}"
        )
    if not isinstance(scenario_type, str):
        raise TypeError(
            f"scenario_type must be a string, "
            f"got {type(scenario_type).__name__}"
        )
    if scenario_type not in SUPPORTED_SCENARIO_DISPATCHES:
        raise ValueError(
            f"Unknown scenario_type '{scenario_type}'. "
            f"Supported: {sorted(SUPPORTED_SCENARIO_DISPATCHES.keys())}"
        )

    method_name = SUPPORTED_SCENARIO_DISPATCHES[scenario_type]
    method = getattr(engine, method_name)

    try:
        result = method(**kwargs)
    except (TypeError, ValueError) as exc:
        return SandboxRunnerResult(
            scenario_type=scenario_type,
            success=False,
            result=None,
            error_message=str(exc),
        )

    return SandboxRunnerResult(
        scenario_type=scenario_type,
        success=True,
        result=result,
        error_message=None,
    )
