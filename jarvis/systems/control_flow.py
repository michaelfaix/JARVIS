# =============================================================================
# jarvis/systems/control_flow.py
# Authority: FAS v6.0.1 -- S17.5, lines 14608-14796
# =============================================================================
#
# SCOPE
# -----
# System control flow through 11 sequential pipeline layers.  Evaluates
# validation gates at each layer and produces control signals.  Early exit
# on any non-CONTINUE signal (hard stop enforcement).
#
# Public symbols:
#   ControlSignal              Enum: CONTINUE, DEGRADE, STOP, EMERGENCY
#   FlowState                  Frozen dataclass for layer state
#   SystemControlFlow          Pipeline flow controller
#
# GOVERNANCE
# ----------
# Control signals are advisory.  EMERGENCY and STOP halt processing.
# DEGRADE switches to defensive mode.  CONTINUE progresses to next layer.
#
# DEPENDENCIES
# ------------
#   stdlib:    dataclasses, enum, typing
#   external:  NONE
#   internal:  jarvis.systems.validation_gates
#   PROHIBITED: logging, random, file IO, network IO, datetime.now(), numpy
#
# DETERMINISM
# -----------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-05  All branching deterministic.
# DET-07  Same inputs = identical output.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique
from typing import Dict, List

from jarvis.systems.validation_gates import (
    QualityGate,
    DriftGate,
    KalmanGate,
    ECEGate,
    OODGate,
    RiskGate,
)

__all__ = [
    "ControlSignal",
    "FlowState",
    "SystemControlFlow",
]


# =============================================================================
# SECTION 1 -- ENUM
# =============================================================================

@unique
class ControlSignal(Enum):
    """
    Control signal type for pipeline flow.

    CONTINUE:   Normal flow progression to next layer.
    DEGRADE:    Reduce functionality, switch to defensive mode.
    STOP:       Halt processing at current layer.
    EMERGENCY:  Critical failure, emergency shutdown.
    """
    CONTINUE = "continue"
    DEGRADE = "degrade"
    STOP = "stop"
    EMERGENCY = "emergency"


# =============================================================================
# SECTION 2 -- DATA TYPES
# =============================================================================

@dataclass(frozen=True)
class FlowState:
    """
    State at a pipeline layer.

    Fields:
        layer:       Current layer number (1+11).
        layer_name:  Human-readable layer name.
        signal:      Control signal for this layer.
        gate_passed: Whether the validation gate passed (True if no gate).
        reason:      Explanation of gate result or progression.
    """
    layer: int
    layer_name: str
    signal: ControlSignal
    gate_passed: bool
    reason: str


# =============================================================================
# SECTION 3 -- LAYER NAMES
# =============================================================================

LAYER_NAMES: Dict[int, str] = {
    1: "data_ingestion",
    2: "features",
    3: "state_estimation",
    4: "regime_detection",
    5: "calibration",
    6: "uncertainty_aggregation",
    7: "ood_detection",
    8: "risk_engine",
    9: "strategy_selection",
    10: "degradation_control",
    11: "output_interface",
}
"""Canonical layer names for the 11-layer pipeline."""


# =============================================================================
# SECTION 4 -- CONTROL FLOW
# =============================================================================

class SystemControlFlow:
    """
    Pipeline control flow through 11 sequential layers.

    Evaluates metrics against validation gates at each gated layer.
    Non-gated layers always CONTINUE.  Early exit on non-CONTINUE signal.

    Stateless: all inputs passed explicitly to execute().
    """

    def execute(
        self,
        quality_score: float,
        drift_severity: float,
        condition_number: float,
        ece: float,
        is_ood: bool,
        var: float,
    ) -> List[FlowState]:
        """
        Execute the full 11-layer pipeline control flow.

        Each gated layer is checked.  If a gate fails, the appropriate
        control signal is emitted and processing halts (early exit).
        Non-gated layers (4, 6, 9, 10, 11) always produce CONTINUE.

        Args:
            quality_score:    Layer 1 data quality metric [0, 1].
            drift_severity:   Layer 2 feature drift metric [0, 1].
            condition_number: Layer 3 Kalman condition number (>= 0).
            ece:              Layer 5 Expected Calibration Error [0, 1].
            is_ood:           Layer 7 OOD detection result (bool).
            var:              Layer 8 Value at Risk (typically negative).

        Returns:
            List of FlowState objects, one per layer traversed.
            Last element indicates where processing stopped.

        Raises:
            TypeError: If arguments have wrong types.
        """
        if not isinstance(quality_score, (int, float)):
            raise TypeError(
                f"quality_score must be numeric, "
                f"got {type(quality_score).__name__}"
            )
        if not isinstance(drift_severity, (int, float)):
            raise TypeError(
                f"drift_severity must be numeric, "
                f"got {type(drift_severity).__name__}"
            )
        if not isinstance(condition_number, (int, float)):
            raise TypeError(
                f"condition_number must be numeric, "
                f"got {type(condition_number).__name__}"
            )
        if not isinstance(ece, (int, float)):
            raise TypeError(
                f"ece must be numeric, "
                f"got {type(ece).__name__}"
            )
        if not isinstance(is_ood, bool):
            raise TypeError(
                f"is_ood must be bool, got {type(is_ood).__name__}"
            )
        if not isinstance(var, (int, float)):
            raise TypeError(
                f"var must be numeric, got {type(var).__name__}"
            )

        states: List[FlowState] = []

        # -- Layer 1: Data Ingestion (QualityGate) --
        gate_result = QualityGate().check(quality_score)
        if gate_result.passed:
            states.append(FlowState(
                layer=1, layer_name=LAYER_NAMES[1],
                signal=ControlSignal.CONTINUE,
                gate_passed=True, reason=gate_result.reason,
            ))
        else:
            states.append(FlowState(
                layer=1, layer_name=LAYER_NAMES[1],
                signal=ControlSignal.STOP,
                gate_passed=False, reason=gate_result.reason,
            ))
            return states

        # -- Layer 2: Features (DriftGate) --
        gate_result = DriftGate().check(drift_severity)
        if gate_result.passed:
            states.append(FlowState(
                layer=2, layer_name=LAYER_NAMES[2],
                signal=ControlSignal.CONTINUE,
                gate_passed=True, reason=gate_result.reason,
            ))
        else:
            states.append(FlowState(
                layer=2, layer_name=LAYER_NAMES[2],
                signal=ControlSignal.DEGRADE,
                gate_passed=False, reason=gate_result.reason,
            ))
            return states

        # -- Layer 3: State Estimation (KalmanGate) --
        gate_result = KalmanGate().check(condition_number)
        if gate_result.passed:
            states.append(FlowState(
                layer=3, layer_name=LAYER_NAMES[3],
                signal=ControlSignal.CONTINUE,
                gate_passed=True, reason=gate_result.reason,
            ))
        else:
            states.append(FlowState(
                layer=3, layer_name=LAYER_NAMES[3],
                signal=ControlSignal.DEGRADE,
                gate_passed=False, reason=gate_result.reason,
            ))
            return states

        # -- Layer 4: Regime Detection (no gate) --
        states.append(FlowState(
            layer=4, layer_name=LAYER_NAMES[4],
            signal=ControlSignal.CONTINUE,
            gate_passed=True, reason="No gate — passthrough",
        ))

        # -- Layer 5: Calibration (ECEGate) --
        gate_result = ECEGate().check(ece)
        if gate_result.passed:
            states.append(FlowState(
                layer=5, layer_name=LAYER_NAMES[5],
                signal=ControlSignal.CONTINUE,
                gate_passed=True, reason=gate_result.reason,
            ))
        else:
            states.append(FlowState(
                layer=5, layer_name=LAYER_NAMES[5],
                signal=ControlSignal.STOP,
                gate_passed=False, reason=gate_result.reason,
            ))
            return states

        # -- Layer 6: Uncertainty Aggregation (no gate) --
        states.append(FlowState(
            layer=6, layer_name=LAYER_NAMES[6],
            signal=ControlSignal.CONTINUE,
            gate_passed=True, reason="No gate — passthrough",
        ))

        # -- Layer 7: OOD Detection (OODGate) --
        gate_result = OODGate().check(is_ood)
        if gate_result.passed:
            states.append(FlowState(
                layer=7, layer_name=LAYER_NAMES[7],
                signal=ControlSignal.CONTINUE,
                gate_passed=True, reason=gate_result.reason,
            ))
        else:
            states.append(FlowState(
                layer=7, layer_name=LAYER_NAMES[7],
                signal=ControlSignal.DEGRADE,
                gate_passed=False, reason=gate_result.reason,
            ))
            return states

        # -- Layer 8: Risk Engine (RiskGate) --
        gate_result = RiskGate().check(var)
        if gate_result.passed:
            states.append(FlowState(
                layer=8, layer_name=LAYER_NAMES[8],
                signal=ControlSignal.CONTINUE,
                gate_passed=True, reason=gate_result.reason,
            ))
        else:
            states.append(FlowState(
                layer=8, layer_name=LAYER_NAMES[8],
                signal=ControlSignal.EMERGENCY,
                gate_passed=False, reason=gate_result.reason,
            ))
            return states

        # -- Layer 9: Strategy Selection (no gate) --
        states.append(FlowState(
            layer=9, layer_name=LAYER_NAMES[9],
            signal=ControlSignal.CONTINUE,
            gate_passed=True, reason="No gate — passthrough",
        ))

        # -- Layer 10: Degradation Control (no gate) --
        states.append(FlowState(
            layer=10, layer_name=LAYER_NAMES[10],
            signal=ControlSignal.CONTINUE,
            gate_passed=True, reason="No gate — passthrough",
        ))

        # -- Layer 11: Output Interface (no gate) --
        states.append(FlowState(
            layer=11, layer_name=LAYER_NAMES[11],
            signal=ControlSignal.CONTINUE,
            gate_passed=True, reason="No gate — passthrough",
        ))

        return states
