# jarvis/research/__init__.py

from jarvis.research.feature_pipeline import (
    FeatureEntry,
    FeatureImportanceResult,
    FeatureRegistry,
)

from jarvis.research.walk_forward_validation import (
    WFV_MIN_OOS_RATIO,
    WFV_MIN_SEGMENTS,
    WFV_MIN_IS_BARS,
    CROSS_ASSET_MIN_POSITIVE,
    ROBUSTNESS_PENALTY,
    WalkForwardSegment,
    WalkForwardResult,
    CrossAssetRobustnessScore,
    WalkForwardValidationEngine,
)

from jarvis.research.overfitting_detector import (
    PERFORMANCE_SPIKE_THRESHOLD,
    PARAM_SENSITIVITY_THRESHOLD,
    OverfittingReport,
    OverfittingDetector,
)

from jarvis.research.scenario_sandbox import (
    SCENARIO_TYPES,
    CORR_FM04_THRESHOLD,
    VOL_FM02_THRESHOLD,
    MODE_MAP,
    ScenarioConfig,
    ScenarioResult,
    ScenarioSandboxEngine,
)

from jarvis.research.sandbox_runner import (
    SUPPORTED_SCENARIO_DISPATCHES,
    SandboxRunnerResult,
    run_scenario_safely,
)

__all__ = [
    "FeatureEntry",
    "FeatureImportanceResult",
    "FeatureRegistry",
    "WFV_MIN_OOS_RATIO",
    "WFV_MIN_SEGMENTS",
    "WFV_MIN_IS_BARS",
    "CROSS_ASSET_MIN_POSITIVE",
    "ROBUSTNESS_PENALTY",
    "WalkForwardSegment",
    "WalkForwardResult",
    "CrossAssetRobustnessScore",
    "WalkForwardValidationEngine",
    "PERFORMANCE_SPIKE_THRESHOLD",
    "PARAM_SENSITIVITY_THRESHOLD",
    "OverfittingReport",
    "OverfittingDetector",
    "SCENARIO_TYPES",
    "CORR_FM04_THRESHOLD",
    "VOL_FM02_THRESHOLD",
    "MODE_MAP",
    "ScenarioConfig",
    "ScenarioResult",
    "ScenarioSandboxEngine",
    "SUPPORTED_SCENARIO_DISPATCHES",
    "SandboxRunnerResult",
    "run_scenario_safely",
]
