# =============================================================================
# jarvis/validation/validators.py — S15 Validation Categories (10)
#
# Authority: FAS v6.0.1, S15
#
# 10 validation categories for system certification:
#   1. ECE Walk-Forward
#   2. Per-Regime ECE
#   3. Historical Crisis Detection
#   4. Synthetic Stress Certification
#   5. OOD Consensus
#   6. System Contract D(t)
#   7. Meta-Uncertainty State Transitions
#   8. Numerical Stability
#   9. Performance
#  10. Logging Integrity
#
# Entry point: run_all_validations()
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
#   stdlib:   dataclasses, math, hashlib
#   internal: NONE
#   external: NONE (pure Python)
# =============================================================================

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

__all__ = [
    "ValidationResult",
    "validate_ece_walkforward",
    "validate_ece_per_regime",
    "validate_crisis_detection",
    "validate_stress_certification",
    "validate_ood_consensus",
    "validate_system_contract",
    "validate_meta_uncertainty_transitions",
    "validate_numerical_stability",
    "validate_performance",
    "validate_logging_integrity",
    "run_all_validations",
]


# =============================================================================
# SECTION 1 -- DATACLASS
# =============================================================================

@dataclass(frozen=True)
class ValidationResult:
    """Result of a single validation check."""
    category: str
    passed: bool
    score: float
    details: str
    n_checks: int
    n_passed: int

    def __post_init__(self) -> None:
        if not isinstance(self.category, str):
            raise TypeError(
                f"ValidationResult.category must be str, "
                f"got {type(self.category).__name__}"
            )
        if not isinstance(self.passed, bool):
            raise TypeError(
                f"ValidationResult.passed must be bool, "
                f"got {type(self.passed).__name__}"
            )
        if not isinstance(self.score, (int, float)):
            raise TypeError(
                f"ValidationResult.score must be numeric, "
                f"got {type(self.score).__name__}"
            )
        if not math.isfinite(self.score):
            raise ValueError(
                f"ValidationResult.score must be finite, got {self.score!r}"
            )
        if not isinstance(self.details, str):
            raise TypeError(
                f"ValidationResult.details must be str, "
                f"got {type(self.details).__name__}"
            )
        if not isinstance(self.n_checks, int):
            raise TypeError(
                f"ValidationResult.n_checks must be int, "
                f"got {type(self.n_checks).__name__}"
            )
        if not isinstance(self.n_passed, int):
            raise TypeError(
                f"ValidationResult.n_passed must be int, "
                f"got {type(self.n_passed).__name__}"
            )


# =============================================================================
# SECTION 2 -- HELPER
# =============================================================================

def _safe_ratio(n_passed: int, n_checks: int) -> float:
    """Compute ratio safely; returns 0.0 if n_checks is 0."""
    if n_checks == 0:
        return 0.0
    return n_passed / n_checks


def _percentile_sorted(values: list, p: float) -> float:
    """
    Compute the p-th percentile from a sorted list of values.
    p in [0, 100]. Uses linear interpolation.
    """
    n = len(values)
    if n == 0:
        return 0.0
    if n == 1:
        return values[0]
    # Rank
    rank = (p / 100.0) * (n - 1)
    lower = int(rank)
    upper = lower + 1
    if upper >= n:
        return values[-1]
    frac = rank - lower
    return values[lower] + frac * (values[upper] - values[lower])


# =============================================================================
# SECTION 3 -- CATEGORY 1: ECE Walk-Forward
# =============================================================================

def validate_ece_walkforward(
    ece_values: tuple,
    threshold: float = 0.05,
    min_pass_rate: float = 0.875,
) -> ValidationResult:
    """
    Category 1: ECE Walk-Forward.
    16 periods, at least 14/16 (87.5%) must have ECE < threshold.
    """
    if not isinstance(ece_values, tuple):
        raise TypeError(
            f"ece_values must be a tuple, got {type(ece_values).__name__}"
        )

    n_checks = len(ece_values)
    n_passed = 0
    for v in ece_values:
        if isinstance(v, (int, float)) and math.isfinite(v) and v < threshold:
            n_passed += 1

    rate = _safe_ratio(n_passed, n_checks)
    passed = rate >= min_pass_rate

    return ValidationResult(
        category="ECE_WALKFORWARD",
        passed=passed,
        score=rate,
        details=(
            f"{n_passed}/{n_checks} periods with ECE < {threshold} "
            f"(rate={rate:.3f}, required={min_pass_rate:.3f})"
        ),
        n_checks=n_checks,
        n_passed=n_passed,
    )


# =============================================================================
# SECTION 4 -- CATEGORY 2: Per-Regime ECE
# =============================================================================

def validate_ece_per_regime(
    regime_eces: dict,
    threshold: float = 0.05,
    drift_threshold: float = 0.02,
) -> ValidationResult:
    """
    Category 2: Per-Regime ECE.
    All regimes must have ECE < threshold.
    Max drift between any two regimes < drift_threshold.
    """
    if not isinstance(regime_eces, dict):
        raise TypeError(
            f"regime_eces must be a dict, got {type(regime_eces).__name__}"
        )

    n_checks = len(regime_eces)
    n_passed = 0
    ece_vals = []

    for regime, ece in regime_eces.items():
        if not isinstance(ece, (int, float)) or not math.isfinite(ece):
            continue
        ece_vals.append(ece)
        if ece < threshold:
            n_passed += 1

    # Drift check: max difference between any two regime ECEs
    max_drift = 0.0
    for i in range(len(ece_vals)):
        for j in range(i + 1, len(ece_vals)):
            drift = abs(ece_vals[i] - ece_vals[j])
            if drift > max_drift:
                max_drift = drift

    drift_ok = max_drift < drift_threshold
    all_below = n_passed == n_checks
    passed = all_below and drift_ok

    # Score: fraction passing with drift penalty
    rate = _safe_ratio(n_passed, n_checks)
    score = rate * (1.0 if drift_ok else 0.5)

    return ValidationResult(
        category="ECE_PER_REGIME",
        passed=passed,
        score=score,
        details=(
            f"{n_passed}/{n_checks} regimes with ECE < {threshold}, "
            f"max_drift={max_drift:.4f} (limit={drift_threshold})"
        ),
        n_checks=n_checks,
        n_passed=n_passed,
    )


# =============================================================================
# SECTION 5 -- CATEGORY 3: Historical Crisis Detection
# =============================================================================

def validate_crisis_detection(
    crisis_ood_scores: tuple,
    threshold: float = 0.6,
) -> ValidationResult:
    """
    Category 3: Historical Crisis Detection.
    All known crisis periods must have OOD score >= threshold.
    """
    if not isinstance(crisis_ood_scores, tuple):
        raise TypeError(
            f"crisis_ood_scores must be a tuple, "
            f"got {type(crisis_ood_scores).__name__}"
        )

    n_checks = len(crisis_ood_scores)
    n_passed = 0
    for s in crisis_ood_scores:
        if isinstance(s, (int, float)) and math.isfinite(s) and s >= threshold:
            n_passed += 1

    rate = _safe_ratio(n_passed, n_checks)
    passed = n_passed == n_checks

    return ValidationResult(
        category="CRISIS_DETECTION",
        passed=passed,
        score=rate,
        details=(
            f"{n_passed}/{n_checks} crisis periods detected "
            f"(OOD score >= {threshold})"
        ),
        n_checks=n_checks,
        n_passed=n_passed,
    )


# =============================================================================
# SECTION 6 -- CATEGORY 4: Synthetic Stress Certification
# =============================================================================

def validate_stress_certification(
    stress_results: tuple,
    min_pass_rate: float = 0.90,
) -> ValidationResult:
    """
    Category 4: Synthetic Stress Certification.
    5 categories x 3 severities = 15 tests.
    At least 90% must pass.
    """
    if not isinstance(stress_results, tuple):
        raise TypeError(
            f"stress_results must be a tuple, "
            f"got {type(stress_results).__name__}"
        )

    n_checks = len(stress_results)
    n_passed = 0
    for r in stress_results:
        # Each result is expected to have a .passed attribute or be a bool
        if hasattr(r, "passed"):
            if r.passed:
                n_passed += 1
        elif isinstance(r, bool) and r:
            n_passed += 1

    rate = _safe_ratio(n_passed, n_checks)
    passed = rate >= min_pass_rate

    return ValidationResult(
        category="STRESS_CERTIFICATION",
        passed=passed,
        score=rate,
        details=(
            f"{n_passed}/{n_checks} stress tests passed "
            f"(rate={rate:.3f}, required={min_pass_rate:.3f})"
        ),
        n_checks=n_checks,
        n_passed=n_passed,
    )


# =============================================================================
# SECTION 7 -- CATEGORY 5: OOD Consensus
# =============================================================================

def validate_ood_consensus(
    sensor_counts: tuple,
    min_sensors: int = 5,
) -> ValidationResult:
    """
    Category 5: OOD Consensus.
    All evaluations must have all 5 sensors reporting.
    """
    if not isinstance(sensor_counts, tuple):
        raise TypeError(
            f"sensor_counts must be a tuple, "
            f"got {type(sensor_counts).__name__}"
        )

    n_checks = len(sensor_counts)
    n_passed = 0
    for count in sensor_counts:
        if isinstance(count, int) and count >= min_sensors:
            n_passed += 1

    rate = _safe_ratio(n_passed, n_checks)
    passed = n_passed == n_checks

    return ValidationResult(
        category="OOD_CONSENSUS",
        passed=passed,
        score=rate,
        details=(
            f"{n_passed}/{n_checks} evaluations with >= {min_sensors} sensors"
        ),
        n_checks=n_checks,
        n_passed=n_passed,
    )


# =============================================================================
# SECTION 8 -- CATEGORY 6: System Contract D(t)
# =============================================================================

def validate_system_contract(
    contract_fields: tuple,
    required: tuple = ("mu", "sigma_squared", "Q", "S", "U", "R"),
) -> ValidationResult:
    """
    Category 6: System Contract D(t).
    All required fields must be present in every prediction.
    """
    if not isinstance(contract_fields, tuple):
        raise TypeError(
            f"contract_fields must be a tuple, "
            f"got {type(contract_fields).__name__}"
        )

    n_checks = len(contract_fields)
    n_passed = 0

    for fields in contract_fields:
        if isinstance(fields, dict):
            has_all = all(f in fields for f in required)
        elif isinstance(fields, (tuple, list, set, frozenset)):
            has_all = all(f in fields for f in required)
        elif hasattr(fields, "__dict__"):
            has_all = all(hasattr(fields, f) for f in required)
        else:
            has_all = False

        if has_all:
            n_passed += 1

    rate = _safe_ratio(n_passed, n_checks)
    passed = n_passed == n_checks

    return ValidationResult(
        category="SYSTEM_CONTRACT",
        passed=passed,
        score=rate,
        details=(
            f"{n_passed}/{n_checks} predictions have all required fields "
            f"{required}"
        ),
        n_checks=n_checks,
        n_passed=n_passed,
    )


# =============================================================================
# SECTION 9 -- CATEGORY 7: Meta-Uncertainty State Transitions
# =============================================================================

_VALID_META_U_ORDER = ("NORMAL", "RECALIBRATION", "CONSERVATIVE", "COLLAPSE")


def validate_meta_uncertainty_transitions(
    transitions: tuple,
) -> ValidationResult:
    """
    Category 7: Meta-Uncertainty State Transitions.
    Verify NORMAL -> RECALIBRATION -> CONSERVATIVE -> COLLAPSE ordering.
    Each transition must go to the same or adjacent state (no skipping).
    """
    if not isinstance(transitions, tuple):
        raise TypeError(
            f"transitions must be a tuple, "
            f"got {type(transitions).__name__}"
        )

    if len(transitions) < 2:
        return ValidationResult(
            category="META_U_TRANSITIONS",
            passed=True,
            score=1.0,
            details="Fewer than 2 transitions; trivially valid",
            n_checks=0,
            n_passed=0,
        )

    n_checks = len(transitions) - 1
    n_passed = 0

    for i in range(n_checks):
        curr = transitions[i]
        nxt = transitions[i + 1]

        if curr not in _VALID_META_U_ORDER or nxt not in _VALID_META_U_ORDER:
            continue

        curr_idx = _VALID_META_U_ORDER.index(curr)
        nxt_idx = _VALID_META_U_ORDER.index(nxt)

        # Valid: same state, or adjacent (up or down by 1)
        if abs(nxt_idx - curr_idx) <= 1:
            n_passed += 1

    rate = _safe_ratio(n_passed, n_checks)
    passed = n_passed == n_checks

    return ValidationResult(
        category="META_U_TRANSITIONS",
        passed=passed,
        score=rate,
        details=(
            f"{n_passed}/{n_checks} transitions are valid "
            f"(adjacent or same state)"
        ),
        n_checks=n_checks,
        n_passed=n_passed,
    )


# =============================================================================
# SECTION 10 -- CATEGORY 8: Numerical Stability
# =============================================================================

def validate_numerical_stability(
    values: tuple,
) -> ValidationResult:
    """
    Category 8: Numerical Stability.
    Check values for NaN/Inf. Zero tolerance.
    """
    if not isinstance(values, tuple):
        raise TypeError(
            f"values must be a tuple, got {type(values).__name__}"
        )

    n_checks = len(values)
    n_passed = 0
    for v in values:
        if isinstance(v, (int, float)) and math.isfinite(v):
            n_passed += 1

    rate = _safe_ratio(n_passed, n_checks)
    passed = n_passed == n_checks

    return ValidationResult(
        category="NUMERICAL_STABILITY",
        passed=passed,
        score=rate,
        details=(
            f"{n_passed}/{n_checks} values are finite "
            f"(zero NaN/Inf tolerance)"
        ),
        n_checks=n_checks,
        n_passed=n_passed,
    )


# =============================================================================
# SECTION 11 -- CATEGORY 9: Performance
# =============================================================================

def validate_performance(
    latencies_fast: tuple,
    latencies_deep: tuple,
    fast_p95: float = 50.0,
    deep_p95: float = 500.0,
) -> ValidationResult:
    """
    Category 9: Performance.
    P95 of fast latencies <= fast_p95 ms.
    P95 of deep latencies <= deep_p95 ms.
    """
    if not isinstance(latencies_fast, tuple):
        raise TypeError(
            f"latencies_fast must be a tuple, "
            f"got {type(latencies_fast).__name__}"
        )
    if not isinstance(latencies_deep, tuple):
        raise TypeError(
            f"latencies_deep must be a tuple, "
            f"got {type(latencies_deep).__name__}"
        )

    n_checks = 2
    n_passed = 0

    # Compute P95 for fast
    fast_sorted = sorted(
        v for v in latencies_fast
        if isinstance(v, (int, float)) and math.isfinite(v)
    )
    fast_p95_val = _percentile_sorted(fast_sorted, 95.0) if fast_sorted else 0.0

    # Compute P95 for deep
    deep_sorted = sorted(
        v for v in latencies_deep
        if isinstance(v, (int, float)) and math.isfinite(v)
    )
    deep_p95_val = _percentile_sorted(deep_sorted, 95.0) if deep_sorted else 0.0

    if fast_p95_val <= fast_p95:
        n_passed += 1
    if deep_p95_val <= deep_p95:
        n_passed += 1

    passed = n_passed == n_checks

    # Score: average of how close to limits (capped at 1.0)
    fast_score = min(1.0, fast_p95 / max(fast_p95_val, 1e-10))
    deep_score = min(1.0, deep_p95 / max(deep_p95_val, 1e-10))
    score = (fast_score + deep_score) / 2.0

    return ValidationResult(
        category="PERFORMANCE",
        passed=passed,
        score=min(1.0, score),
        details=(
            f"Fast P95={fast_p95_val:.1f}ms (limit={fast_p95}ms), "
            f"Deep P95={deep_p95_val:.1f}ms (limit={deep_p95}ms)"
        ),
        n_checks=n_checks,
        n_passed=n_passed,
    )


# =============================================================================
# SECTION 12 -- CATEGORY 10: Logging Integrity
# =============================================================================

def validate_logging_integrity(
    event_hashes: tuple,
) -> ValidationResult:
    """
    Category 10: Logging Integrity.
    Hash chain must be valid (each hash depends on previous).
    100% integrity required.

    Each element is expected to be a string hash. The chain is valid if
    hash(event_hashes[i-1] + event_hashes[i]) produces a consistent chain.
    For this validator, we check that consecutive hashes are non-empty
    strings and that the sequence is non-repeating (basic integrity).
    """
    if not isinstance(event_hashes, tuple):
        raise TypeError(
            f"event_hashes must be a tuple, "
            f"got {type(event_hashes).__name__}"
        )

    if len(event_hashes) < 2:
        return ValidationResult(
            category="LOGGING_INTEGRITY",
            passed=True,
            score=1.0,
            details="Fewer than 2 hashes; trivially valid",
            n_checks=max(len(event_hashes), 0),
            n_passed=max(len(event_hashes), 0),
        )

    n_checks = len(event_hashes) - 1
    n_passed = 0

    for i in range(1, len(event_hashes)):
        prev = event_hashes[i - 1]
        curr = event_hashes[i]

        # Basic validation: both must be non-empty strings
        if not isinstance(prev, str) or not isinstance(curr, str):
            continue
        if not prev or not curr:
            continue

        # Check chain: the current hash should incorporate the previous
        # We verify by checking that a deterministic hash of
        # (prev + "::" + position) matches the stored hash
        expected = hashlib.sha256(
            (prev + "::" + str(i)).encode("utf-8")
        ).hexdigest()

        if curr == expected:
            n_passed += 1

    rate = _safe_ratio(n_passed, n_checks)
    passed = n_passed == n_checks

    return ValidationResult(
        category="LOGGING_INTEGRITY",
        passed=passed,
        score=rate,
        details=(
            f"{n_passed}/{n_checks} hash chain links verified"
        ),
        n_checks=n_checks,
        n_passed=n_passed,
    )


# =============================================================================
# SECTION 13 -- RUN ALL VALIDATIONS
# =============================================================================

def run_all_validations(data: dict) -> tuple:
    """
    Run all 10 validation categories, return tuple of ValidationResult.

    Expected data keys:
        ece_values:          tuple of float (Category 1)
        regime_eces:         dict (Category 2)
        crisis_ood_scores:   tuple of float (Category 3)
        stress_results:      tuple (Category 4)
        sensor_counts:       tuple of int (Category 5)
        contract_fields:     tuple of dict (Category 6)
        transitions:         tuple of str (Category 7)
        numerical_values:    tuple of float (Category 8)
        latencies_fast:      tuple of float (Category 9)
        latencies_deep:      tuple of float (Category 9)
        event_hashes:        tuple of str (Category 10)
    """
    if not isinstance(data, dict):
        raise TypeError(
            f"data must be a dict, got {type(data).__name__}"
        )

    results = []

    # Category 1: ECE Walk-Forward
    results.append(validate_ece_walkforward(
        data.get("ece_values", ()),
    ))

    # Category 2: Per-Regime ECE
    results.append(validate_ece_per_regime(
        data.get("regime_eces", {}),
    ))

    # Category 3: Crisis Detection
    results.append(validate_crisis_detection(
        data.get("crisis_ood_scores", ()),
    ))

    # Category 4: Stress Certification
    results.append(validate_stress_certification(
        data.get("stress_results", ()),
    ))

    # Category 5: OOD Consensus
    results.append(validate_ood_consensus(
        data.get("sensor_counts", ()),
    ))

    # Category 6: System Contract
    results.append(validate_system_contract(
        data.get("contract_fields", ()),
    ))

    # Category 7: Meta-Uncertainty Transitions
    results.append(validate_meta_uncertainty_transitions(
        data.get("transitions", ()),
    ))

    # Category 8: Numerical Stability
    results.append(validate_numerical_stability(
        data.get("numerical_values", ()),
    ))

    # Category 9: Performance
    results.append(validate_performance(
        data.get("latencies_fast", ()),
        data.get("latencies_deep", ()),
    ))

    # Category 10: Logging Integrity
    results.append(validate_logging_integrity(
        data.get("event_hashes", ()),
    ))

    return tuple(results)
