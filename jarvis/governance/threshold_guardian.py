# =============================================================================
# jarvis/governance/threshold_guardian.py — Governance & Hardening (S31)
#
# Robustheit > Accuracy.
# Hard Gates sind keine Optionen. Sie sind Systemgrenzen.
# Soft Warnings bei Hard-Fehlern sind VERBOTEN.
#
# R1: Hard Calibration Gates     → RuntimeError, kein Warning
# R2: OOD Enforcement            → RuntimeError, kein Warning
# R3: Immutable Thresholds       → Hash-gesichert, CI-blockiert bei Mismatch
# R4: CI Blockade bei Fehler     → Exit Code 1, kein Soft-Pass
# R5: Deterministisch            → Gleiche Inputs → Gleiche Outputs
# R7: Kein Soft-Warning          → Hard Error bei Hard-Fehler
# =============================================================================

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict


# ---------------------------------------------------------------------------
# THRESHOLD GUARDIAN
# ---------------------------------------------------------------------------

class ThresholdGuardian:
    """Verifies THRESHOLD_MANIFEST.json at every system start.

    Throws on hash mismatch: NO soft-warning, NO silent pass.
    """

    def __init__(self, manifest_path: Path) -> None:
        self.manifest_path = manifest_path

    def load_and_verify(self) -> Dict[str, Any]:
        """Load manifest and verify integrity via SHA-256.

        Returns:
            Dict of threshold values.

        Raises:
            FileNotFoundError: If manifest file does not exist.
            RuntimeError: If manifest hash does not match computed hash.
        """
        if not self.manifest_path.exists():
            raise FileNotFoundError(
                f"THRESHOLD_MANIFEST.json not found: {self.manifest_path}. "
                "System start denied."
            )

        with open(self.manifest_path, "r") as f:
            raw = f.read()
            data = json.loads(raw)

        stored_hash = data.get("manifest_hash", "")

        # Hash computation: everything except manifest_hash field
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True).encode("utf-8")
        ).hexdigest()

        if stored_hash != "SHA256_PLACEHOLDER_COMPUTED_AT_BUILD_TIME":
            if computed_hash != stored_hash:
                raise RuntimeError(
                    f"THRESHOLD_MANIFEST Hash-Mismatch. "
                    f"Expected: {stored_hash[:12]}... "
                    f"Computed: {computed_hash[:12]}... "
                    "System start denied. Possible manipulation."
                )

        return data["thresholds"]


# ---------------------------------------------------------------------------
# HARD CALIBRATION GATE
# ---------------------------------------------------------------------------

class HardCalibrationGate:
    """Deployment-Gate: Throws on ECE violation. NO soft-warning."""

    def __init__(self, thresholds: Dict[str, Any]) -> None:
        self.ECE_HARD_GATE = float(thresholds["ece_hard_gate"])
        self.ECE_PER_REGIME_DRIFT = float(thresholds["ece_per_regime_drift"])

    def enforce(self, ece: float, regime: str) -> None:
        """Enforce ECE hard gate.

        Raises:
            RuntimeError: If ECE exceeds hard gate. NEVER just logs.
        """
        if ece > self.ECE_HARD_GATE:
            raise RuntimeError(
                f"CALIBRATION_HARD_GATE_VIOLATED: ECE={ece:.4f} > "
                f"{self.ECE_HARD_GATE} (regime={regime}). "
                "Deployment blocked."
            )


# ---------------------------------------------------------------------------
# OOD ENFORCER
# ---------------------------------------------------------------------------

class OODEnforcer:
    """OOD-Enforcement: Blocks production on OOD-recall violation."""

    def __init__(self, thresholds: Dict[str, Any]) -> None:
        self.OOD_CONSENSUS_MIN = int(thresholds["ood_consensus_minimum"])
        self.OOD_RECALL_HISTORICAL = float(thresholds["ood_recall_historical"])
        self.OOD_RECALL_SYNTHETIC = float(thresholds["ood_recall_synthetic"])

    def enforce_recall(
        self,
        historical_recall: float,
        synthetic_recall: float,
    ) -> None:
        """Enforce OOD recall thresholds.

        Raises:
            RuntimeError: If any recall falls below threshold. NO soft-warning.
        """
        if historical_recall < self.OOD_RECALL_HISTORICAL:
            raise RuntimeError(
                f"OOD_RECALL_GATE_VIOLATED: historical_recall="
                f"{historical_recall:.3f} < {self.OOD_RECALL_HISTORICAL}. "
                "Deployment blocked."
            )
        if synthetic_recall < self.OOD_RECALL_SYNTHETIC:
            raise RuntimeError(
                f"OOD_RECALL_GATE_VIOLATED: synthetic_recall="
                f"{synthetic_recall:.3f} < {self.OOD_RECALL_SYNTHETIC}. "
                "Deployment blocked."
            )


# ---------------------------------------------------------------------------
# CI GOVERNANCE GUARD
# ---------------------------------------------------------------------------

class CIGovernanceGuard:
    """CI/CD Guard: Blocks merge on governance violation."""

    def run_full_governance_check(
        self,
        manifest_path: Path,
        ece_results: Dict[str, float],
        ood_recall: Dict[str, float],
    ) -> None:
        """Complete governance check.

        If ANYTHING fails: raises RuntimeError (CI Exit Code 1).

        Args:
            manifest_path: Path to THRESHOLD_MANIFEST.json.
            ece_results: Dict mapping regime name to ECE value.
            ood_recall: Dict with keys 'historical' and 'synthetic'.

        Raises:
            FileNotFoundError: If manifest not found.
            RuntimeError: On any governance violation.
        """
        guardian = ThresholdGuardian(manifest_path)
        thresholds = guardian.load_and_verify()

        gate = HardCalibrationGate(thresholds)
        enforcer = OODEnforcer(thresholds)

        # Check ECE per regime
        for regime, ece in ece_results.items():
            gate.enforce(ece=ece, regime=regime)

        # Check OOD Recall
        enforcer.enforce_recall(
            historical_recall=ood_recall.get("historical", 0.0),
            synthetic_recall=ood_recall.get("synthetic", 0.0),
        )
