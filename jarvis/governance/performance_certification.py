# =============================================================================
# jarvis/governance/performance_certification.py — Performance Certification (S36)
#
# Deployment NIEMALS ohne vollstaendige Zertifizierung.
# Alle 8 Zertifizierungs-Kriterien muessen bestanden werden.
# Kein Soft-Warning. Nur Hard-Block.
#
# DET-06: All certification thresholds are fixed literals.
# PROHIBITED-05: No global mutable state.
# =============================================================================

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class CertificationResult:
    """Complete certification result."""

    model_id: str
    timestamp: str
    calibration_ok: bool  # ECE < 0.05
    ood_ok: bool  # Recall >= 0.90
    stress_ok: bool  # All scenarios passed
    monte_carlo_ok: bool  # VaR95 within limit
    slippage_ok: bool  # Slippage within budget
    capital_alloc_ok: bool  # Allocation engine certified
    reproducibility_ok: bool  # Deterministic + reproducible
    integrity_ok: bool  # Hash-chain + manifest verified
    all_passed: bool  # True if ALL 8 passed
    deployment_cleared: bool  # Equivalent to all_passed
    failures: List[str]
    certification_hash: str


class PerformanceCertificationEngine:
    """Deployment certification: 8 mandatory criteria.

    No deployment without all_passed == True.
    No soft-warning. Only hard-block.
    """

    # Certification thresholds (hash-protected in THRESHOLD_MANIFEST.json)
    ECE_LIMIT = 0.05
    OOD_RECALL_LIMIT = 0.90
    MONTE_CARLO_VAR_LIMIT = -0.20  # Max -20% VaR95
    MAX_SLIPPAGE_PCT = 0.01  # Max 1% Slippage

    def certify(
        self,
        model_id: str,
        ece: float,
        ood_recall_historical: float,
        ood_recall_synthetic: float,
        stress_scenarios_passed: List[str],
        stress_scenarios_required: List[str],
        monte_carlo_var95: float,
        avg_slippage_pct: float,
        capital_alloc_validated: bool,
        reproducibility_hash: str,
        integrity_hash: str,
        expected_integrity_hash: str,
    ) -> CertificationResult:
        """Check all 8 certification criteria.

        Returns CertificationResult on success.
        Raises RuntimeError if deployment_cleared == False (hard-block).

        Args:
            model_id: Model identifier.
            ece: Expected Calibration Error.
            ood_recall_historical: OOD recall on historical data.
            ood_recall_synthetic: OOD recall on synthetic data.
            stress_scenarios_passed: List of passed stress scenario names.
            stress_scenarios_required: List of required stress scenario names.
            monte_carlo_var95: Monte Carlo VaR at 95% confidence.
            avg_slippage_pct: Average slippage percentage.
            capital_alloc_validated: Whether capital allocation is validated.
            reproducibility_hash: Reproducibility hash (empty string = not set).
            integrity_hash: Computed integrity hash.
            expected_integrity_hash: Expected integrity hash.

        Returns:
            CertificationResult with all 8 gate results.

        Raises:
            RuntimeError: If any gate fails (DEPLOYMENT_BLOCKED).
        """
        failures: List[str] = []

        # 1. Calibration
        calibration_ok = ece < self.ECE_LIMIT
        if not calibration_ok:
            failures.append(
                f"CALIBRATION: ECE={ece:.4f} >= {self.ECE_LIMIT}"
            )

        # 2. OOD
        ood_ok = (
            ood_recall_historical >= self.OOD_RECALL_LIMIT
            and ood_recall_synthetic >= self.OOD_RECALL_LIMIT
        )
        if not ood_ok:
            failures.append(
                f"OOD: hist={ood_recall_historical:.3f}, "
                f"synth={ood_recall_synthetic:.3f} "
                f"(limit={self.OOD_RECALL_LIMIT})"
            )

        # 3. Stress Tests
        missing_scenarios = (
            set(stress_scenarios_required) - set(stress_scenarios_passed)
        )
        stress_ok = len(missing_scenarios) == 0
        if not stress_ok:
            failures.append(
                f"STRESS: Fehlende Szenarien: {missing_scenarios}"
            )

        # 4. Monte Carlo
        monte_carlo_ok = monte_carlo_var95 >= self.MONTE_CARLO_VAR_LIMIT
        if not monte_carlo_ok:
            failures.append(
                f"MONTE_CARLO: VaR95={monte_carlo_var95:.3f} "
                f"< {self.MONTE_CARLO_VAR_LIMIT}"
            )

        # 5. Slippage
        slippage_ok = avg_slippage_pct <= self.MAX_SLIPPAGE_PCT
        if not slippage_ok:
            failures.append(
                f"SLIPPAGE: {avg_slippage_pct:.4f} > {self.MAX_SLIPPAGE_PCT}"
            )

        # 6. Capital Allocation
        capital_alloc_ok = capital_alloc_validated
        if not capital_alloc_ok:
            failures.append("CAPITAL_ALLOCATION: Nicht validiert")

        # 7. Reproducibility
        reproducibility_ok = bool(reproducibility_hash)
        if not reproducibility_ok:
            failures.append(
                "REPRODUCIBILITY: Kein Reproduzierbarkeits-Hash"
            )

        # 8. Integrity
        integrity_ok = integrity_hash == expected_integrity_hash
        if not integrity_ok:
            failures.append(
                f"INTEGRITY: Hash-Mismatch. "
                f"Erwartet={expected_integrity_hash[:8]}..., "
                f"Berechnet={integrity_hash[:8]}..."
            )

        all_passed = len(failures) == 0

        # Certification hash
        cert_data = {
            "model_id": model_id,
            "ece": ece,
            "ood_hist": ood_recall_historical,
            "ood_synth": ood_recall_synthetic,
            "stress_ok": stress_ok,
            "var95": monte_carlo_var95,
            "all_passed": all_passed,
        }
        cert_hash = hashlib.sha256(
            json.dumps(cert_data, sort_keys=True).encode()
        ).hexdigest()[:16]

        result = CertificationResult(
            model_id=model_id,
            timestamp=datetime.utcnow().isoformat(),
            calibration_ok=calibration_ok,
            ood_ok=ood_ok,
            stress_ok=stress_ok,
            monte_carlo_ok=monte_carlo_ok,
            slippage_ok=slippage_ok,
            capital_alloc_ok=capital_alloc_ok,
            reproducibility_ok=reproducibility_ok,
            integrity_ok=integrity_ok,
            all_passed=all_passed,
            deployment_cleared=all_passed,
            failures=failures,
            certification_hash=cert_hash,
        )

        # Hard Block: NO deployment without certification
        if not all_passed:
            raise RuntimeError(
                f"DEPLOYMENT_BLOCKED fuer '{model_id}'. "
                f"Fehlgeschlagene Gates ({len(failures)}): "
                + "; ".join(failures)
            )

        return result
