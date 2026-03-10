# =============================================================================
# jarvis/learning/deterministic_learning.py — Deterministic Learning Architecture (S27)
#
# Controlled, deterministic learning cycle with audit trail and rollback.
# NO uncontrolled live self-learning.
#
# 7-Step Cycle:
#   1. Training in Chunks (controlled)
#   2. Validation (ECE-Gate)
#   3. Stress-Test (historical crises)
#   4. Comparison with active version
#   5. Deployment ONLY with clear improvement
#   6. Drift-Monitoring (continuous)
#   7. Rollback always possible
# =============================================================================

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional


# ---------------------------------------------------------------------------
# DATACLASS
# ---------------------------------------------------------------------------

@dataclass
class LearningCycleResult:
    """Result of a single deterministic learning cycle."""

    cycle_id: str
    timestamp: str
    ece_before: float
    ece_after: float
    stress_pass: bool
    improvement: float
    deployed: bool
    rollback_available: bool
    model_hash: str
    notes: str


# ---------------------------------------------------------------------------
# ORCHESTRATOR
# ---------------------------------------------------------------------------

class DeterministicLearningOrchestrator:
    """Controlled learning cycle with audit trail and rollback capability.

    All gates are enforced in strict order:
        1. ECE-Gate (hard limit)
        2. Stress-Test
        3. Improvement threshold
    Only after all gates pass is deployment executed.
    """

    # Immutable gates (DET-06 — fixed literals, NOT parameterizable)
    MIN_IMPROVEMENT_THRESHOLD: float = 0.005
    MAX_ECE_AFTER_TRAINING: float = 0.05
    REQUIRED_STRESS_PASS: bool = True

    def __init__(self, model_registry_path: Path, log_layer) -> None:
        self.registry_path: Path = model_registry_path
        self.log = log_layer
        self._active_model_hash: Optional[str] = None
        self._active_params: Optional[Dict[str, Any]] = None
        self._rollback_snapshot: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    # PUBLIC: run_cycle
    # ------------------------------------------------------------------

    def run_cycle(
        self,
        new_model_params: Dict[str, Any],
        validation_data: Dict[str, Any],
        stress_test_fn: Callable,
        calibration_eval_fn: Callable,
        chunk_id: str,
    ) -> LearningCycleResult:
        """Execute one deterministic learning cycle.

        Gate order (mandatory):
            1. ECE-Gate  →  RuntimeError if ece_after > MAX_ECE_AFTER_TRAINING
            2. Stress-Test  →  RuntimeError if stress_test_fn returns False
            3. Improvement  →  no-deploy result if improvement < threshold

        Args:
            new_model_params: Candidate model parameters.
            validation_data: Data dict for validation & stress testing.
            stress_test_fn: Callable(model=str, data=dict) → bool.
            calibration_eval_fn: Callable(model=str, data=dict) → float (ECE).
            chunk_id: Identifier for the training chunk.

        Returns:
            LearningCycleResult with deployment outcome.

        Raises:
            RuntimeError: On ECE-Gate or Stress-Test failure.
        """
        # Step 1 — Generate cycle_id & timestamp
        timestamp = datetime.utcnow().isoformat()
        raw = f"{chunk_id}{timestamp}"
        cycle_id = hashlib.sha256(raw.encode()).hexdigest()[:12]

        # Step 2 — ECE evaluation
        ece_before = calibration_eval_fn(model="active", data=validation_data)
        ece_after = calibration_eval_fn(model="candidate", data=validation_data)

        # Gate 1 — ECE hard limit
        if ece_after > self.MAX_ECE_AFTER_TRAINING:
            self.log.log_event(
                type="LEARNING_GATE_FAIL",
                reason="ECE_ABOVE_HARD_LIMIT",
                cycle_id=cycle_id,
                ece_after=ece_after,
            )
            raise RuntimeError(
                f"LEARNING_GATE_FAIL: ECE nach Training = {ece_after:.4f} "
                f"> {self.MAX_ECE_AFTER_TRAINING} (Hard Limit)"
            )

        # Gate 2 — Stress-Test
        stress_pass = stress_test_fn(model="candidate", data=validation_data)
        if not stress_pass and self.REQUIRED_STRESS_PASS:
            self.log.log_event(
                type="LEARNING_GATE_FAIL",
                reason="STRESS_TEST_FAILED",
                cycle_id=cycle_id,
            )
            raise RuntimeError(
                "LEARNING_GATE_FAIL: Stress-Test nicht bestanden"
            )

        # Step 4 — Improvement check
        improvement = ece_before - ece_after

        if improvement < self.MIN_IMPROVEMENT_THRESHOLD:
            self.log.log_event(
                type="LEARNING_NO_DEPLOY",
                reason="INSUFFICIENT_IMPROVEMENT",
                improvement=improvement,
                cycle_id=cycle_id,
            )
            return LearningCycleResult(
                cycle_id=cycle_id,
                timestamp=timestamp,
                ece_before=ece_before,
                ece_after=ece_after,
                stress_pass=stress_pass,
                improvement=improvement,
                deployed=False,
                rollback_available=True,
                model_hash="CANDIDATE_NOT_DEPLOYED",
                notes=(
                    f"Nicht deployt: Verbesserung {improvement:.4f} "
                    f"< {self.MIN_IMPROVEMENT_THRESHOLD}"
                ),
            )

        # Step 5 — Deployment
        param_json = json.dumps(new_model_params, sort_keys=True)
        new_model_hash = hashlib.sha256(param_json.encode()).hexdigest()[:16]

        self._save_rollback_snapshot()
        self._deploy(new_model_params, new_model_hash)
        self._active_model_hash = new_model_hash

        self.log.log_event(
            type="LEARNING_DEPLOYED",
            model_hash=new_model_hash,
            ece_improvement=improvement,
            cycle_id=cycle_id,
        )

        return LearningCycleResult(
            cycle_id=cycle_id,
            timestamp=timestamp,
            ece_before=ece_before,
            ece_after=ece_after,
            stress_pass=stress_pass,
            improvement=improvement,
            deployed=True,
            rollback_available=True,
            model_hash=new_model_hash,
            notes=f"Deployt mit ECE-Verbesserung {improvement:.4f}",
        )

    # ------------------------------------------------------------------
    # PUBLIC: rollback
    # ------------------------------------------------------------------

    def rollback(self) -> bool:
        """Roll back to last stable version.

        Returns:
            True if rollback succeeded, False if no snapshot available.
        """
        snapshot = self._load_rollback_snapshot()
        if snapshot is None:
            self.log.log_event(
                type="ROLLBACK_FAILED",
                reason="NO_SNAPSHOT_AVAILABLE",
            )
            return False

        self._deploy(snapshot["params"], snapshot["hash"])
        self._active_model_hash = snapshot["hash"]
        self._active_params = snapshot["params"]

        self.log.log_event(
            type="ROLLBACK_SUCCESS",
            restored_hash=snapshot["hash"],
        )
        return True

    # ------------------------------------------------------------------
    # PRIVATE: persistence (isolated from core logic)
    # ------------------------------------------------------------------

    def _save_rollback_snapshot(self) -> None:
        """Save current model state snapshot for rollback."""
        if self._active_model_hash is not None:
            self._rollback_snapshot = {
                "params": self._active_params,
                "hash": self._active_model_hash,
            }

    def _load_rollback_snapshot(self) -> Optional[Dict[str, Any]]:
        """Load last saved model snapshot."""
        return self._rollback_snapshot

    def _deploy(self, params: Dict[str, Any], model_hash: str) -> None:
        """Deploy model parameters (activate in system)."""
        self._active_params = params
        self._active_model_hash = model_hash
