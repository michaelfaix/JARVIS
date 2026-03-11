# JARVIS — Multi-Asset Strategy Platform (MASP) v6.1.0

Decision Quality Platform for deterministic strategy research and portfolio analysis.

> **P0 Classification:** Pure analysis and research platform. No broker API, no real-money management, no order execution.

---

## Architecture

JARVIS follows a strict layered architecture with a directed acyclic import graph. Every computation is deterministic (DET-01..DET-07): no stochastic operations, no external state, no side effects, bit-identical replay guaranteed.

```
Tier 1  STABLE CORE (FREEZE)     core/, utils/
Tier 2  RISK ENGINE (FREEZE)     risk/
Tier 3  ALLOCATION               portfolio/, execution/
Tier 4  ORCHESTRATION             orchestrator/, governance/
Tier 5  EXTERNAL LAYERS           backtest/, walkforward/, metrics/, strategy/,
                                  selection/, optimization/, robustness/, report/
Tier 6  ANALYSIS & RESEARCH       simulation/, intelligence/, confidence/,
                                  learning/, systems/, research/, chart/
DVH     VERIFICATION              verification/
```

### Import Rules

```
orchestrator/  -> core/, risk/, execution/
backtest/      -> core/, orchestrator/
walkforward/   -> core/, backtest/, orchestrator/
execution/     -> core/, portfolio/
portfolio/     -> (stdlib only)
risk/          -> core/, utils/
utils/         -> core/
core/          -> (stdlib only)
```

Upward imports (e.g. core/ importing from orchestrator/) are forbidden. Circular imports are forbidden.

---

## Module Structure

### Tier 1 -- Stable Core (`jarvis/core/`)

| Module | Purpose |
|---|---|
| `regime.py` | `GlobalRegimeState`, `CorrelationRegimeState` enums |
| `regime_detector.py` | HMM-based regime detection |
| `state_layer.py` | `LatentState` frozen dataclass |
| `state_estimator.py` | Kalman-style state estimation |
| `volatility_tracker.py` | EWMA volatility tracker |
| `data_layer.py` | Data abstraction layer |
| `feature_layer.py` | Technical feature computation (RSI, ATR, MACD, CCI, OBV, ...) |
| `integrity_layer.py` | Hash-chain validation |
| `execution_guard.py` | Execution safety guard |
| `logging_layer.py` | Structured logging |
| `decision_context_state.py` | `DecisionContextState` frozen dataclass |
| `system_mode.py` | `SystemMode` enum + `GlobalSystemStateController` |
| `risk_layer/` | Risk subdomain (domain models, evaluator, sizing, exceptions) |

### Tier 1 -- Constants (`jarvis/utils/`)

| Module | Purpose |
|---|---|
| `constants.py` | `JOINT_RISK_MULTIPLIER_TABLE` + platform constants |

### Tier 2 -- Risk Engine (`jarvis/risk/`)

| Module | Purpose |
|---|---|
| `risk_engine.py` | `RiskEngine.assess()` -- main risk assessment (FREEZE v6.1.0) |
| `THRESHOLD_MANIFEST.json` | Hash-protected thresholds (MAX_DRAWDOWN, VOL_COMPRESSION, SHOCK_CAP) |
| `correlation.py` | `DynamicCorrelationModel`, `_pearson()` |
| `stress_detector.py` | 4-dimension explicit stress detection |
| `tail_risk.py` | Tail risk analysis |
| `portfolio_risk.py` | Portfolio-level risk aggregation |
| `capital_allocation.py` | Risk-based capital allocation |
| `asset_risk.py`, `gap_risk.py`, `systemic_risk.py` | Specialized risk modules |

### Tier 3 -- Allocation (`jarvis/portfolio/`, `jarvis/execution/`)

| Module | Purpose |
|---|---|
| `portfolio_allocator.py` | `allocate_positions()` -- canonical allocation function |
| `exposure_router.py` | `route_exposure_to_positions()` -- canonical routing |

### Tier 4 -- Orchestration (`jarvis/orchestrator/`, `jarvis/governance/`)

| Module | Purpose |
|---|---|
| `pipeline.py` | `run_full_pipeline()` -- main API entry point v1.2.1 |
| `policy_validator.py` | `validate_pipeline_config()` -- GOV-01..GOV-06 |
| `threshold_guardian.py` | Hash-protected threshold enforcement |
| `model_registry.py` | Model governance and ECE validation |
| `performance_certification.py` | Deployment certification gates |

### Tier 5 -- External Layers

| Module | Purpose |
|---|---|
| `backtest/engine.py` | `run_backtest()` -- single-asset rolling-window backtest |
| `backtest/multi_asset_engine.py` | `run_multi_asset_backtest()`, `run_multi_asset_walkforward()` |
| `walkforward/engine.py` | `generate_windows()`, `run_walkforward()` |
| `metrics/engine.py` | `sharpe_ratio()`, `max_drawdown()`, `calmar_ratio()`, `compute_metrics()` |
| `metrics/ece_calculator.py` | `compute_ece()` -- Expected Calibration Error (adaptive binning) |
| `metrics/fragility_index.py` | `StructuralFragilityIndex` -- 4-dimension fragility assessment |
| `metrics/trust_score.py` | `TrustScoreEngine` -- composite trust scoring |
| `strategy/engine.py` | `momentum_signal()`, `mean_reversion_signal()`, `combine_signals()` |
| `selection/engine.py` | `rank_candidates()`, `filter_by_threshold()`, `select_top_n()` |
| `optimization/engine.py` | `run_optimization()` -- Cartesian product parameter search |
| `robustness/engine.py` | `evaluate_robustness()` -- parameter stability analysis |
| `report/engine.py` | `generate_report()` -- consumes `compute_metrics()` |

### Tier 6 -- Analysis & Research

| Module | Purpose |
|---|---|
| `simulation/strategy_lab.py` | Monte Carlo, slippage, walk-forward, stress test |
| `simulation/stress_scenarios.py` | 8 named stress presets (2008, COVID, Flash Crash, ...) |
| `intelligence/decision_quality_engine.py` | `DecisionQualityEngine` (< 20ms/cycle) |
| `intelligence/regime_duration_model.py` | `RegimeDurationModel` |
| `intelligence/ood_engine.py` | Out-of-distribution detection |
| `confidence/adaptive_selectivity_model.py` | `AdaptiveSelectivityModel` |
| `strategy/signal_fragility_analyzer.py` | `SignalFragilityAnalyzer` (< 30ms/eval) |
| `systems/mode_controller.py` | `ModeController` -- 4-mode operational FSM |
| `systems/reproducibility.py` | `ReproducibilityController` -- float precision guard |
| `systems/control_flow.py` | Layer-by-layer execution pipeline |
| `systems/validation_gates.py` | ECE gate, stress gate, OOD gate |
| `learning/deterministic_learning.py` | Deterministic model training with ECE gates |
| `research/scenario_sandbox.py` | Isolated scenario sandbox |
| `research/overfitting_detector.py` | Overfitting detection |

### DVH -- Deterministic Verification Harness (`jarvis/verification/`)

| Module | Purpose |
|---|---|
| `run_harness.py` | Entry point -- 37 input vectors, bit-identical replay |
| `manifest_validator.py` | THRESHOLD_MANIFEST hash verification |
| `input_vector_generator.py` | Deterministic test vector generation |
| `execution_recorder.py` | Record execution traces |
| `replay_engine.py` | Replay and compare against records |
| `bit_comparator.py` | Bit-level output comparison |
| `clip_verifier.py` | Clip chain order verification (INV-07) |

---

## Quick Start

```python
from jarvis.orchestrator.pipeline import run_full_pipeline
from jarvis.core.regime import GlobalRegimeState

positions = run_full_pipeline(
    returns_history=[0.01, -0.02, 0.015, -0.005] * 10,  # min 20 elements
    current_regime=GlobalRegimeState.RISK_ON,
    meta_uncertainty=0.2,
    total_capital=100_000.0,
    asset_prices={"BTC": 65000.0, "ETH": 3200.0, "SPY": 520.0},
)
# Returns: {"BTC": 0.307, "ETH": 6.25, "SPY": 38.46}
```

### RiskEngine Direct

```python
from jarvis.risk.risk_engine import RiskEngine
from jarvis.core.regime import GlobalRegimeState

result = RiskEngine().assess(
    returns_history=[0.01, -0.02, 0.015, -0.005] * 10,
    current_regime=GlobalRegimeState.RISK_ON,
    meta_uncertainty=0.2,
)
# result.exposure_weight, result.risk_regime, result.volatility_forecast
```

### Multi-Asset Backtest

```python
from jarvis.backtest import run_multi_asset_backtest
from jarvis.core.regime import GlobalRegimeState

result = run_multi_asset_backtest(
    asset_returns={"BTC": returns_btc, "ETH": returns_eth},
    asset_prices={"BTC": prices_btc, "ETH": prices_eth},
    window=20,
    initial_capital=100_000.0,
    regime=GlobalRegimeState.RISK_ON,
    meta_uncertainty=0.2,
)
# result.portfolio_equity, result.asset_results, result.portfolio_metrics
```

### Stress Scenarios

```python
from jarvis.simulation import StrategyLab, get_scenario

lab = StrategyLab()
preset = get_scenario("2008_FINANCIAL_CRISIS")
result = lab.stress_test(
    scenario_name=preset.name,
    scenario_returns=list(preset.returns),
    strategy_fn=lambda r: r,
    drawdown_limit=0.15,
)
# result.survived, result.max_drawdown, result.pnl_impact
```

### ECE Calibration Check

```python
from jarvis.metrics import compute_ece

result = compute_ece(
    confidences=[0.9, 0.8, 0.7, 0.6, 0.5],
    outcomes=[1.0, 1.0, 0.0, 1.0, 0.0],
)
# result.ece, result.is_calibrated, result.bin_statistics
```

---

## Tests

```bash
# Run all tests
pytest

# Verbose with short traceback
pytest -v --tb=short

# Single module
pytest tests/unit/metrics/test_ece_calculator.py -v

# Coverage report
pytest --cov=jarvis --cov-report=term-missing

# Stop on first failure
pytest -x -q
```

## Deterministic Verification Harness

```bash
python -m jarvis.verification.run_harness \
  --manifest-path jarvis/risk/THRESHOLD_MANIFEST.json \
  --module-version 6.1.0 \
  --runs-dir jarvis/verification/runs
```

Verifies 37 input vectors with bit-identical replay against recorded execution traces. Must pass before any deployment.

---

## Quality Metrics

| Metric | Value |
|---|---|
| Tests | 7,025 |
| Production code | ~38,500 lines |
| Test code | ~60,500 lines |
| Test:Code ratio | 1.6:1 |
| Python modules | 124 |
| DVH vectors | 37 |
| Stress presets | 8 (5 historical + 3 synthetic) |
| Determinism | DET-01..DET-07 enforced |
| ECE hard gate | < 0.05 |

---

## Tech Stack

- **Python** 3.10+ (developed on 3.12)
- **Core dependencies:** numpy >= 1.24, scipy >= 1.10
- **Testing:** pytest 9.0.2, pytest-cov
- **Mutation testing:** mutmut 3.5
- **DVH:** stdlib only (zero third-party dependencies)

---

## Regime Types

```python
class GlobalRegimeState(Enum):
    RISK_ON     # Normal risk-on environment
    RISK_OFF    # Risk-off environment
    CRISIS      # Crisis regime (75% dampening on exposure)
    TRANSITION  # Transition phase
    UNKNOWN     # Unknown state
```

## Hash-Protected Thresholds

| Constant | Value | Purpose |
|---|---|---|
| `MAX_DRAWDOWN_THRESHOLD` | 0.15 | 15% hard drawdown limit |
| `VOL_COMPRESSION_TRIGGER` | 0.30 | 30% ann. vol triggers compression |
| `SHOCK_EXPOSURE_CAP` | 0.25 | Max 25% exposure under shock |
| `ECE_HARD_GATE` | 0.05 | Calibration error limit |
| `ECE_PER_REGIME_DRIFT` | 0.02 | Max per-regime ECE drift |

These constants are hash-protected in `THRESHOLD_MANIFEST.json` and verified by the DVH on every run.

---

*MASP v6.1.0 | Harness v1.0.0 | FAS v6.0.1*
