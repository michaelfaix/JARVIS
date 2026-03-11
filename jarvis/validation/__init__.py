# =============================================================================
# jarvis/validation/__init__.py — S15 Validation Layer
#
# Authority: FAS v6.0.1, S15
#
# CLASSIFICATION: Tier 6 — ANALYSIS AND STRATEGY RESEARCH TOOL.
# =============================================================================

from jarvis.validation.metrics import (
    ValidationMetrics,
    VetoResult,
    VETO_ECE_THRESHOLD,
    VETO_ECE_DRIFT_THRESHOLD,
    VETO_CALIBRATION_STABILITY,
    VETO_OOD_RECALL,
    VETO_REGIME_DETECTION,
    VETO_FAST_P95_MS,
    VETO_DEEP_P95_MS,
    check_veto_criteria,
)
from jarvis.validation.validators import (
    ValidationResult,
    validate_ece_walkforward,
    validate_ece_per_regime,
    validate_crisis_detection,
    validate_stress_certification,
    validate_ood_consensus,
    validate_system_contract,
    validate_meta_uncertainty_transitions,
    validate_numerical_stability,
    validate_performance,
    validate_logging_integrity,
    run_all_validations,
)
from jarvis.validation.stress import (
    StressScenario,
    StressResult,
    STRESS_CATEGORIES,
    SEVERITY_LEVELS,
    generate_stress_scenarios,
    run_stress_scenario,
    run_stress_certification,
    get_certification_summary,
)

__all__ = [
    # metrics.py
    "ValidationMetrics",
    "VetoResult",
    "VETO_ECE_THRESHOLD",
    "VETO_ECE_DRIFT_THRESHOLD",
    "VETO_CALIBRATION_STABILITY",
    "VETO_OOD_RECALL",
    "VETO_REGIME_DETECTION",
    "VETO_FAST_P95_MS",
    "VETO_DEEP_P95_MS",
    "check_veto_criteria",
    # validators.py
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
    # stress.py
    "StressScenario",
    "StressResult",
    "STRESS_CATEGORIES",
    "SEVERITY_LEVELS",
    "generate_stress_scenarios",
    "run_stress_scenario",
    "run_stress_certification",
    "get_certification_summary",
]
