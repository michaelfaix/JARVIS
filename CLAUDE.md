# JARVIS — Multi-Asset Strategy Platform (MASP)
# Decision Quality Platform v6.2.0
# CLAUDE.md — Projektkontext für Claude Code

---

## SYSTEM CLASSIFICATION (P0 — UNVERAENDERLICH)

**JARVIS ist ein reines Analyse- und Strategie-Forschungsplattform.**
- KEIN Handelssystem. KEIN Broker-API. KEIN Echtgeld-Management.
- Alle Berechnungen operieren auf simulierten Positionen.
- Dieser P0-Status überschreibt alle anderen Layer (P1-P9).
- Jeder Code-Pfad der zu echten Order-Übertragungen führt ist ein kritischer Verstoss.

---

## Projektstruktur

```
JARVIS/
├── jarvis/
│   ├── core/               <- STABLE CORE (FREEZE - nicht ohne Release aendern!)
│   │   ├── regime.py               GlobalRegimeState, AssetRegimeState, AssetClass,
│   │   │                           CorrelationRegimeState, HierarchicalRegime Enums
│   │   ├── regime_detector.py      RegimeDetector (HMM-basiert)
│   │   ├── state_layer.py          LatentState dataclass
│   │   ├── state_estimator.py      StateEstimator (Kalman-artig)
│   │   ├── volatility_tracker.py   VolatilityTracker (EWMA)
│   │   ├── data_layer.py           OHLCV, MarketData, EnhancedMarketData, DataCache
│   │   ├── data_structures.py      Shared data structures
│   │   ├── feature_layer.py        FeatureLayer, FeatureDriftMonitor, DriftResult
│   │   ├── feature_registry.py     Feature registry
│   │   ├── integrity_layer.py      Hash-Chain Validierung
│   │   ├── logging_layer.py        EventLogger, Event, EventFilter
│   │   ├── execution_guard.py      build_execution_order(), ExecutionOrder
│   │   ├── decision_context_state.py  DecisionContextState (frozen dataclass)
│   │   ├── system_mode.py          SystemMode Enum + GlobalSystemStateController
│   │   ├── trading_calendar.py     is_trading_day(), NYSE/CME/EUREX Holiday-Listen
│   │   ├── strategy_schema.py      Strategy schema definitions
│   │   ├── strategy_registry.py    Strategy registry
│   │   ├── schema_versions.py      Schema versioning
│   │   ├── event_bus.py            Event bus
│   │   ├── event_log.py            Event log
│   │   ├── event_queue.py          Event queue
│   │   ├── confidence_refresh.py   Confidence refresh logic
│   │   ├── global_state.py         Global state definitions
│   │   ├── global_state_controller.py  Global state controller
│   │   ├── governance_monitor.py   Governance monitoring
│   │   ├── hybrid_coordinator.py   Hybrid mode coordinator
│   │   ├── live_data_integrity_gate.py  Live data integrity gate
│   │   ├── market_data_provider.py Market data provider
│   │   ├── state_checkpoint.py     State checkpoint
│   │   ├── state_refresh_policy.py State refresh policy
│   │   └── risk_layer/             Risk-Layer Subdomain
│   │       ├── domain.py           RiskDomain Datenmodelle
│   │       ├── engine.py           Risk-Layer Engine
│   │       ├── evaluator.py        Risk Evaluator
│   │       ├── exceptions.py       Risk Exceptions
│   │       └── sizing.py           Position Sizing
│   │
│   ├── risk/               <- STABLE CORE (FREEZE - FAS v6.1.0)
│   │   ├── risk_engine.py          RiskEngine - FREEZE v6.1.0 (HAUPTKOMPONENTE)
│   │   ├── THRESHOLD_MANIFEST.json Hash-geschuetzte Konstanten
│   │   ├── correlation.py          _pearson() cross-asset correlation
│   │   ├── asset_risk.py           Asset-level risk
│   │   ├── capital_allocation.py   Capital allocation
│   │   ├── confidence_zone_engine.py  Confidence zone engine
│   │   ├── gap_risk.py             Gap risk detection
│   │   ├── multi_timeframe.py      Multi-timeframe risk
│   │   ├── portfolio_heatmap.py    Portfolio heatmap
│   │   ├── portfolio_risk.py       Portfolio risk
│   │   ├── risk_budget.py          Risk budget
│   │   ├── stress_detector.py      Stress detection
│   │   ├── systemic_risk.py        Systemic risk
│   │   └── tail_risk.py            Tail risk
│   │
│   ├── utils/              <- STABLE CORE (FREEZE)
│   │   └── constants.py            JOINT_RISK_MULTIPLIER_TABLE + Plattform-Konstanten
│   │
│   ├── portfolio/          <- STABLE CORE (FREEZE)
│   │   └── portfolio_allocator.py  allocate_positions() - KANONISCHE Funktion
│   │
│   ├── execution/          <- STABLE CORE (FREEZE)
│   │   ├── exposure_router.py      route_exposure_to_positions() - KANONISCH
│   │   ├── execution_optimizer.py  Execution optimization
│   │   └── session_aware_executor.py  Session-aware execution
│   │
│   ├── governance/         <- Governance Layer
│   │   ├── policy_validator.py     validate_pipeline_config() - GOV-01..GOV-06
│   │   ├── exceptions.py           GovernanceViolationError
│   │   ├── backtest_governance.py  BacktestGovernanceEngine, OverfittingReport
│   │   ├── model_registry.py       Model registry
│   │   ├── performance_certification.py  Performance certification
│   │   └── threshold_guardian.py   Threshold guardian
│   │
│   ├── orchestrator/       <- External Orchestration Layer
│   │   └── pipeline.py             run_full_pipeline() - Haupt-API v1.2.1
│   │
│   ├── backtest/           <- External Layer (IMPLEMENTIERT)
│   │   ├── engine.py               run_backtest() + slippage_model Integration
│   │   └── multi_asset_engine.py   run_multi_asset_backtest(), run_multi_asset_walkforward()
│   │
│   ├── intelligence/       <- Intelligence Layer (IMPLEMENTIERT - MA-1..MA-4)
│   │   ├── ood_engine.py           AssetConditionalOOD (5-Sensor Majority Voting)
│   │   ├── ood_config.py           AssetOODConfig, Thresholds, Weights
│   │   ├── decision_quality_engine.py  DecisionQualityEngine (< 20ms/cycle)
│   │   ├── regime_duration_model.py    RegimeDurationModel
│   │   ├── asset_regimes.py        Asset regime detection
│   │   ├── bayesian_confidence.py  Bayesian confidence estimation
│   │   ├── correlation_regime.py   Correlation regime detection
│   │   ├── cross_asset_layer.py    Cross-asset intelligence
│   │   ├── epistemic_uncertainty.py Epistemic uncertainty estimation
│   │   ├── global_regime.py        Global regime detection
│   │   ├── liquidity_layer.py      Liquidity layer
│   │   ├── macro_layer.py          Macro event layer
│   │   ├── microstructure_layer.py Microstructure analysis
│   │   ├── multi_broker_layer.py   Multi-broker layer
│   │   ├── news_layer.py           News event layer
│   │   ├── regime_memory.py        Regime memory
│   │   ├── regime_transition.py    Regime transition detection
│   │   ├── volatility_markov.py    Volatility Markov model
│   │   └── weight_posterior.py     Weight posterior estimation
│   │
│   ├── confidence/         <- Confidence Layer (IMPLEMENTIERT)
│   │   ├── adaptive_selectivity_model.py  AdaptiveSelectivityModel
│   │   └── failure_impact.py       Failure impact analysis
│   │
│   ├── simulation/         <- Simulation Layer (IMPLEMENTIERT)
│   │   ├── strategy_lab.py         StrategyLab, SlippageModel, MonteCarloResult,
│   │   │                           StressTestResult, WalkForwardResult
│   │   └── stress_scenarios.py     StressScenarioPreset, RegimeAwareScenario,
│   │                               run_regime_aware_stress_test(), SCENARIO_REGISTRY
│   │
│   ├── metrics/            <- Metrics Layer (IMPLEMENTIERT)
│   │   ├── engine.py               compute_metrics(), sharpe_ratio, max_drawdown,
│   │   │                           calmar_ratio, regime_conditional_returns
│   │   ├── ece_calculator.py       ECEResult, compute_ece, compute_ece_scalar
│   │   ├── fragility_index.py      FragilityAssessment, StructuralFragilityIndex
│   │   └── trust_score.py          TrustScoreEngine, TrustScoreResult
│   │
│   ├── strategy/           <- Strategy Layer (IMPLEMENTIERT)
│   │   ├── engine.py               momentum_signal, mean_reversion_signal,
│   │   │                           combine_signals, run_strategy()
│   │   ├── signal_fragility_analyzer.py  SignalFragilityAnalyzer (< 30ms/eval)
│   │   └── adaptive_strategy.py    Adaptive strategy logic
│   │
│   ├── selection/          <- Selection Layer (IMPLEMENTIERT)
│   │   └── engine.py               rank_candidates, filter_by_threshold,
│   │                               select_top_n, run_selection()
│   │
│   ├── optimization/       <- Optimization Layer (IMPLEMENTIERT)
│   │   └── engine.py               run_optimization() - Kartesisches Produkt
│   │
│   ├── robustness/         <- Robustness Layer (IMPLEMENTIERT)
│   │   └── engine.py               evaluate_robustness()
│   │
│   ├── report/             <- Report Layer (IMPLEMENTIERT)
│   │   └── engine.py               generate_report(), generate_enriched_report(),
│   │                               ReportResult (frozen dataclass)
│   │
│   ├── walkforward/        <- Walk-Forward Layer (IMPLEMENTIERT)
│   │   └── engine.py               generate_windows(), generate_trading_windows(),
│   │                               run_walkforward()
│   │
│   ├── models/             <- Models Layer (IMPLEMENTIERT)
│   │   └── calibration.py          Model calibration
│   │
│   ├── learning/           <- Learning Layer (IMPLEMENTIERT)
│   │   └── deterministic_learning.py  Deterministic learning
│   │
│   ├── systems/            <- Systems Layer (IMPLEMENTIERT)
│   │   ├── control_flow.py         Control flow management
│   │   ├── mode_controller.py      Mode controller
│   │   ├── reproducibility.py      Reproducibility guarantees
│   │   └── validation_gates.py     Validation gates
│   │
│   ├── research/           <- Research Layer (IMPLEMENTIERT)
│   │   ├── feature_pipeline.py     Feature pipeline
│   │   ├── overfitting_detector.py Overfitting detection
│   │   ├── sandbox_runner.py       Sandbox runner
│   │   ├── scenario_sandbox.py     Scenario sandbox
│   │   └── walk_forward_validation.py  Walk-forward validation
│   │
│   ├── chart/              <- Chart Layer (IMPLEMENTIERT)
│   │   ├── chart_contract.py       Chart contract definitions
│   │   └── chart_data_builder.py   Chart data builder
│   │
│   └── verification/       <- Deterministic Verification Harness (DVH) v1.0.0
│       ├── run_harness.py          Entry Point
│       ├── manifest_validator.py   Manifest-Pruefung
│       ├── ci_dvh_gate.py          CI DVH gate
│       ├── input_vector_generator.py
│       ├── execution_recorder.py
│       ├── replay_engine.py
│       ├── bit_comparator.py
│       ├── clip_verifier.py
│       ├── failure_handler.py
│       ├── harness_version.py
│       ├── data_models/            Dataclasses fuer DVH
│       ├── vectors/                Input Vector Definitionen
│       ├── storage/                Record Serialisierung
│       └── runs/                   Laufzeit-generierte Verifikations-Records
│
├── tests/                  <- Test Suite (7513 Tests, pytest)
│   ├── test_pipeline_contract.py     Haupt-Vertragstest (Pipeline + Backtest)
│   ├── test_metrics_engine.py        Metrics engine tests
│   ├── test_strategy_engine.py       Strategy engine tests
│   ├── test_selection_engine.py      Selection engine tests
│   ├── test_optimization_engine.py   Optimization engine tests
│   ├── test_robustness_engine.py     Robustness engine tests
│   ├── test_report_engine.py         Report engine tests
│   ├── test_walkforward_engine.py    Walk-forward engine tests
│   ├── test_decision_quality_engine.py  DQE tests
│   ├── test_adaptive_selectivity_model.py  ASM tests
│   ├── test_regime_duration_model.py    RDM tests
│   ├── test_signal_fragility_analyzer.py  SFA tests
│   ├── test_decision_context_state.py   DCS tests
│   ├── test_system_mode.py           SystemMode tests
│   ├── test_multi_asset_integration.py  Multi-asset integration
│   ├── test_ma8_coverage_benchmarks.py  MA-8 coverage benchmarks
│   ├── test_mutant_killers.py        Mutation test killers
│   ├── integration/
│   │   ├── test_full_flow.py         Full pipeline flow (41 tests, determinism)
│   │   └── test_e2e_fas_pipeline.py  End-to-end FAS pipeline
│   └── unit/
│       ├── backtest/                 Backtest tests (multi-asset, slippage)
│       ├── chart/                    Chart tests
│       ├── confidence/               Confidence tests (failure impact)
│       ├── core/                     Core layer tests (30+ test files)
│       ├── execution/                Execution tests
│       ├── governance/               Governance tests (6 test files)
│       ├── intelligence/             Intelligence tests (18 test files)
│       ├── metrics/                  Metrics tests (ECE, fragility, trust score)
│       ├── models/                   Models tests (calibration)
│       ├── report/                   Report tests (enriched report)
│       ├── research/                 Research tests (5 test files)
│       ├── risk/                     Risk tests (10 test files)
│       ├── risk_layer/               Risk layer tests
│       ├── simulation/               Simulation tests (strategy lab, stress, regime-aware)
│       ├── strategy/                 Strategy tests (adaptive, det-learning)
│       └── systems/                  Systems tests (control flow, mode, reproducibility)
│
├── mutants/                <- Mutation Testing (mutmut) - Spiegelstruktur von tests/
├── FAS/                    <- Formale Architektur-Spezifikation (BAUANLEITUNG)
│   ├── FAS_v6_1_0_Risk_Engine.docx
│   ├── DVH_Architecture_Risk_Engine_v6_1_0.docx
│   ├── DVH_Implementation_Blueprint_Risk_Engine_v6_1_0.docx
│   ├── MASTER_FAS_v6_1_0_G_Governance_Integration.docx
│   └── JARVIS_FAS_v6_0_1_Phase6A.txt
├── docs/governance/
│   └── MASTER_FAS_v6_1_0.docx
├── scripts/
│   ├── run_ci.bat
│   └── run_ci_checks.py
├── requirements.txt
├── pytest.ini
├── setup.cfg
└── usage_example.py
```

---

## Tech Stack

- **Sprache:** Python 3.10+
- **Kern-Dependencies:** numpy >= 1.24.0, scipy >= 1.10.0
- **Test-Framework:** pytest 9.0.2, pytest-cov (7513 Tests)
- **Mutation Testing:** mutmut 3.5.0
- **DVH:** Standard Library only (null third-party dependencies)
- **Weitere:** pandas, click, rich, textual, libcst, PyYAML

---

## Architektur-Prinzipien (STRENG EINHALTEN)

### Import-Regeln (gerichteter azyklischer Graph)
```
orchestrator/  -> core/, risk/, execution/
backtest/      -> core/, orchestrator/, metrics/, risk/, walkforward/,
                  governance/, simulation/
walkforward/   -> core/, governance/
simulation/    -> core/, orchestrator/
report/        -> metrics/, simulation/
intelligence/  -> core/
confidence/    -> (nur stdlib)
execution/     -> core/, portfolio/
portfolio/     -> (nur stdlib)
risk/          -> core/, utils/
metrics/       -> (nur stdlib + math)
strategy/      -> core/
selection/     -> (nur stdlib)
optimization/  -> (nur stdlib)
robustness/    -> (nur stdlib)
systems/       -> core/
models/        -> (nur stdlib + math)
learning/      -> core/
research/      -> core/, metrics/
chart/         -> core/
utils/         -> core/
core/          -> (nur stdlib)
```

**VERBOTENE Imports:**
- core/, risk/, utils/, portfolio/, execution/ duerfen NIEMALS aus orchestrator/, backtest/, walkforward/ importieren
- Zirkulaere Imports sind absolut verboten

### Determinismus-Garantien (DET-01 bis DET-07)
1. **DET-01** Keine stochastischen Operationen (kein random(), numpy.random, secrets, os.urandom)
2. **DET-02** Kein externer State-Zugriff innerhalb von Berechnungsfunktionen - alle Inputs explizit uebergeben
3. **DET-03** Keine Seiteneffekte - Berechnungsfunktionen schreiben nicht in externen State
4. **DET-04** Alle Arithmetik-Operationen sind deterministisch (kein symbolisches Math, kein lazy eval)
5. **DET-05** Alle bedingten Verzweigungen sind deterministische Funktionen expliziter Inputs
6. **DET-06** Fixe Literale als Algorithmus-Parameter werden NICHT parametrisierbar gemacht
7. **DET-07** Rueckwaertskompatibilitaet: Gleiche Inputs = bit-identische Outputs (ohne Version-Bump)

### VERBOTENE Aktionen (absolut, keine Ausnahmen)
| Nr | Verbot |
|----|--------|
| PROHIBITED-01 | Stochastische Operationen (random, Monte Carlo, Sampling) |
| PROHIBITED-02 | File I/O in Berechnungs-Layern (open(), pathlib, csv, json, pickle...) |
| PROHIBITED-03 | Logging in Berechnungs-Layern (logging.getLogger, print(), sys.stderr) |
| PROHIBITED-04 | Environment Variable Zugriff (os.environ, os.getenv, dotenv) |
| PROHIBITED-05 | Globaler mutabler State (module-level mutable containers) |
| PROHIBITED-06 | Reimplementierung kanonischer Logik (immer aus dem kanonischen Owner importieren) |
| PROHIBITED-07 | Aenderung von hash-geschuetzten Konstanten zur Laufzeit |
| PROHIBITED-08 | Neue Regime-Enum-Definitionen ausserhalb von jarvis/core/regime.py |
| PROHIBITED-09 | String-basiertes Regime-Branching (immer Enum-Instanzen aus core/regime.py) |
| PROHIBITED-10 | Architektur-Drift (keine neuen Dependency-Edges ohne Review) |

---

## Haupt-API

### run_full_pipeline (Hauptfunktion)
```python
from jarvis.orchestrator.pipeline import run_full_pipeline
from jarvis.core.regime import GlobalRegimeState

positions = run_full_pipeline(
    returns_history=[0.01, -0.02, 0.015, ...],  # min 20 Elemente!
    current_regime=GlobalRegimeState.RISK_ON,
    meta_uncertainty=0.2,                        # [0.0, 1.0]
    total_capital=100_000.0,                     # > 0
    asset_prices={"BTC": 65000.0, "ETH": 3200.0, "SPY": 520.0},
)
# Returns: {"BTC": 0.307, "ETH": 6.25, "SPY": 38.46}
```

### RiskEngine direkt
```python
from jarvis.risk.risk_engine import RiskEngine
from jarvis.core.regime import GlobalRegimeState

engine = RiskEngine()
result = engine.assess(
    returns_history=[...],                    # min 20 Elemente
    current_regime=GlobalRegimeState.RISK_ON,
    meta_uncertainty=0.2,
)
# result.exposure_weight    -> finale Exposure [0, 1]
# result.risk_regime        -> "NORMAL" | "ELEVATED" | "CRITICAL" | "DEFENSIVE"
# result.volatility_forecast -> EWMA annualisierte Volatilitaet
```

### Backtest (mit optionalem Slippage)
```python
from jarvis.backtest.engine import run_backtest
from jarvis.simulation.strategy_lab import SlippageModel

equity_curve = run_backtest(
    returns_series=[...],
    asset_price_series=[...],
    regime=GlobalRegimeState.RISK_ON,
    meta_uncertainty=0.2,
    initial_capital=100_000.0,
    window=20,
    slippage_model=SlippageModel(0.001, 0.01, 0.001),  # optional
)
```

### Multi-Asset Backtest
```python
from jarvis.backtest.multi_asset_engine import run_multi_asset_backtest

result = run_multi_asset_backtest(
    asset_returns={"SPY": [...], "BTC": [...]},
    asset_prices={"SPY": [...], "BTC": [...]},
    window=20, initial_capital=100_000.0,
    regime=GlobalRegimeState.RISK_ON, meta_uncertainty=0.2,
    slippage_model=None,  # optional
)
# result.portfolio_equity, result.asset_results, result.correlation_final
```

### Enriched Report
```python
from jarvis.report.engine import generate_enriched_report

report = generate_enriched_report(
    equity_curve=[100.0, 105.0, ...],
    returns=[0.05, -0.02, ...],              # optional
    regime_labels=["RISK_ON", "CRISIS", ...], # optional
    stress_results=[...],                     # optional
    trust_ece=0.03, trust_ood_recall=0.85,    # optional (all 5 together)
    trust_prediction_variance=0.05,
    trust_drawdown=0.10, trust_uptime=0.99,
)
# report.metrics, report.regime_returns, report.stress_results, report.trust_score
```

### Trading Calendar
```python
from jarvis.core.trading_calendar import is_trading_day, EXCHANGE_NYSE
import datetime

ordinal = datetime.date(2024, 12, 25).toordinal()
is_trading_day(ordinal, EXCHANGE_NYSE)  # False (Christmas)
```

### Trading-Day-Aligned Walk-Forward
```python
from jarvis.walkforward.engine import generate_trading_windows

windows = generate_trading_windows(
    date_ordinals=[...],  # sequence of date ordinals
    train_days=60, test_days=20, step_days=20,
    exchange="NYSE",
)
```

### Regime-Aware Stress Test
```python
from jarvis.simulation.stress_scenarios import run_regime_aware_stress_test, REGIME_AWARE_REGISTRY

scenario = REGIME_AWARE_REGISTRY["FINANCIAL_CRISIS_2008"]
result = run_regime_aware_stress_test(scenario)
# result.equity_curve, result.peak_drawdown, result.n_regime_changes
```

### OOD Detection (5-Sensor Majority Voting)
```python
from jarvis.intelligence.ood_engine import AssetConditionalOOD

detector = AssetConditionalOOD()
result = detector.detect(
    asset_class=AssetClass.EQUITY,
    features=[...], reference_mean=[...], reference_std=[...],
    recent_return=-0.05, current_volatility=0.4,
    historical_volatility=0.2, liquidity_score=0.3,
    macro_event_scores={"FOMC": 0.8},
    regime=hierarchical_regime,
    drift_score=0.7,  # optional, activates 5-sensor voting
)
# result.is_ood, result.score, result.severity, result.components
```

### Verification Harness
```bash
python -m jarvis.verification.run_harness \
  --manifest-path jarvis/risk/THRESHOLD_MANIFEST.json \
  --module-version 6.1.0 \
  --runs-dir jarvis/verification/runs
```

---

## Globale Regime-Typen (aus jarvis/core/regime.py)

```python
class GlobalRegimeState(Enum):
    RISK_ON     # Normales Risk-On Umfeld
    RISK_OFF    # Risk-Off Umfeld
    CRISIS      # Krisen-Regime (75% CRISIS-Dampening auf exposure_weight)
    TRANSITION  # Uebergangsphase
    UNKNOWN     # Unbekannt

class AssetClass(Enum):
    EQUITY, FIXED_INCOME, COMMODITY, CRYPTO, FX

class AssetRegimeState(Enum):
    NORMAL, HIGH_VOLATILITY, SHOCK, RECOVERY

class CorrelationRegimeState(Enum):
    NORMAL, DECORRELATION, BREAKDOWN, CONVERGENCE
```

---

## Hash-Geschuetzte Konstanten (THRESHOLD_MANIFEST.json)

Diese Konstanten sind hash-geschuetzt und duerfen NIEMALS ohne Version-Bump und Manifest-Update geaendert werden:

| Konstante | Wert | Bedeutung |
|-----------|------|-----------|
| MAX_DRAWDOWN_THRESHOLD | 0.15 | 15% - Hard Limit |
| VOL_COMPRESSION_TRIGGER | 0.30 | 30% ann. Vol -> Risk Compression |
| SHOCK_EXPOSURE_CAP | 0.25 | Max 25% Exposure (Clip C Floor) |

**Fixe Literale (FAS DET-06, nicht parametrisierbar):**
- VOL_ADJUSTMENT_CAP = 3.0
- CRISIS_DAMPENING = 0.75
- CLIP_B_FLOOR = 1e-6

---

## Clip Chain Order (INV-07 - Reihenfolge darf NICHT geaendert werden)

```
E_pre_clip = capital_base * vol_efficiency * uncertainty_penalty * regime_budget
  | Clip A: compute_adaptive_position_size() (position_size_factor)
  | Clip B: np.clip(E_pre_clip, 1e-6, 1.0) [IMMER, bedingungslos]
  | Clip C: np.clip(E/JRM, SHOCK_EXPOSURE_CAP, 1.0) [nur wenn JRM aktiv]
  | CRISIS Dampening: * 0.75 [nur wenn CRISIS Regime]
  = exposure_weight (Output)
```

---

## Tests ausfuehren

```bash
# Alle Tests (7513 Tests)
pytest

# Mit Coverage
pytest --cov=jarvis --cov-report=term-missing

# Einzelner Test
pytest tests/test_pipeline_contract.py -v

# Mutation Tests (dauert laenger)
cd mutants && mutmut run

# CI Check Script
python scripts/run_ci_checks.py
```

---

## Governance Rules (GOV-01 bis GOV-06)

| Regel | Feld | Constraint |
|-------|------|-----------|
| GOV-01 | meta_uncertainty | Muss in [0.0, 1.0] liegen |
| GOV-02 | initial_capital | Muss strikt positiv (> 0.0) sein |
| GOV-03 | window | Muss Integer und >= 20 sein |
| GOV-04 | step | Muss Integer und >= 1, <= window sein |
| GOV-05 | regime | Muss GlobalRegimeState Instanz sein |
| GOV-06 | CRISIS + meta | CRISIS ist valides Regime; meta=0.1 ist legitim |

---

## Vollstaendig implementierte Module

### Tier 1 - Stable Core (FREEZE)
- core/regime.py - Regime Enums (GlobalRegimeState, AssetClass, AssetRegimeState, CorrelationRegimeState, HierarchicalRegime)
- core/regime_detector.py - HMM-basierter Regime Detector
- core/state_layer.py - LatentState
- core/state_estimator.py - StateEstimator
- core/volatility_tracker.py - EWMA Volatility Tracker
- core/data_layer.py - OHLCV, MarketData, EnhancedMarketData, DataCache
- core/feature_layer.py - FeatureLayer, FeatureDriftMonitor
- core/integrity_layer.py - Hash-Chain Validierung
- core/risk_layer/ - Risk Layer Subdomain (domain, engine, evaluator, exceptions, sizing)
- risk/risk_engine.py - RiskEngine v6.1.0 (FREEZE)
- utils/constants.py - JOINT_RISK_MULTIPLIER_TABLE + Plattform-Konstanten
- portfolio/portfolio_allocator.py - allocate_positions()
- execution/exposure_router.py - route_exposure_to_positions()

### Tier 2 - Governance + Orchestration
- governance/policy_validator.py - validate_pipeline_config() GOV-01..GOV-06
- governance/backtest_governance.py - BacktestGovernanceEngine, OverfittingReport
- governance/model_registry.py - Model registry
- governance/performance_certification.py - Performance certification
- governance/threshold_guardian.py - Threshold guardian
- orchestrator/pipeline.py - run_full_pipeline() v1.2.1

### Tier 3 - External Layers (ehemals Scaffolds - ALLE IMPLEMENTIERT)
- metrics/engine.py - compute_metrics(), sharpe_ratio, max_drawdown, calmar_ratio, regime_conditional_returns
- metrics/ece_calculator.py - ECEResult, compute_ece, compute_ece_scalar
- metrics/fragility_index.py - FragilityAssessment, StructuralFragilityIndex
- metrics/trust_score.py - TrustScoreEngine, TrustScoreResult
- strategy/engine.py - momentum_signal, mean_reversion_signal, combine_signals, run_strategy()
- strategy/signal_fragility_analyzer.py - SignalFragilityAnalyzer (< 30ms/eval)
- strategy/adaptive_strategy.py - Adaptive strategy
- selection/engine.py - rank_candidates, filter_by_threshold, select_top_n, run_selection()
- optimization/engine.py - run_optimization() (Kartesisches Produkt)
- robustness/engine.py - evaluate_robustness()
- report/engine.py - generate_report(), generate_enriched_report(), ReportResult
- walkforward/engine.py - generate_windows(), generate_trading_windows(), run_walkforward()

### Tier 4 - Backtest + Simulation
- backtest/engine.py - run_backtest() + slippage_model Integration
- backtest/multi_asset_engine.py - run_multi_asset_backtest(), run_multi_asset_walkforward()
- simulation/strategy_lab.py - StrategyLab, SlippageModel, MonteCarloResult, StressTestResult
- simulation/stress_scenarios.py - StressScenarioPreset, RegimeAwareScenario, run_regime_aware_stress_test(), SCENARIO_REGISTRY, REGIME_AWARE_REGISTRY

### Tier 5 - Intelligence (MA-1..MA-4)
- intelligence/ood_engine.py - AssetConditionalOOD (5-Sensor Majority Voting mit FeatureDrift)
- intelligence/ood_config.py - AssetOODConfig, SENSOR_DETECTION_THRESHOLD, OOD_CONSENSUS_MINIMUM
- intelligence/decision_quality_engine.py - DecisionQualityEngine (< 20ms/cycle)
- intelligence/regime_duration_model.py - RegimeDurationModel
- intelligence/bayesian_confidence.py - Bayesian confidence
- intelligence/correlation_regime.py - Correlation regime detection
- intelligence/cross_asset_layer.py - Cross-asset intelligence
- intelligence/epistemic_uncertainty.py - Epistemic uncertainty
- intelligence/global_regime.py - Global regime detection
- intelligence/asset_regimes.py - Asset regime detection
- intelligence/liquidity_layer.py - Liquidity analysis
- intelligence/macro_layer.py - Macro event layer
- intelligence/microstructure_layer.py - Microstructure analysis
- intelligence/multi_broker_layer.py - Multi-broker layer
- intelligence/news_layer.py - News event layer
- intelligence/regime_memory.py - Regime memory
- intelligence/regime_transition.py - Regime transition
- intelligence/volatility_markov.py - Volatility Markov model
- intelligence/weight_posterior.py - Weight posterior

### Tier 6 - Decision Quality + Systems (Phase 3)
- confidence/adaptive_selectivity_model.py - AdaptiveSelectivityModel
- confidence/failure_impact.py - Failure impact analysis
- core/decision_context_state.py - DecisionContextState (frozen dataclass)
- core/system_mode.py - SystemMode Enum + GlobalSystemStateController
- core/trading_calendar.py - is_trading_day(), NYSE/CME/EUREX Holiday-Listen (DET-06 Tuples)
- systems/control_flow.py - Control flow management
- systems/mode_controller.py - Mode controller
- systems/reproducibility.py - Reproducibility guarantees
- systems/validation_gates.py - Validation gates
- models/calibration.py - Model calibration
- learning/deterministic_learning.py - Deterministic learning
- research/ - Feature pipeline, overfitting detector, sandbox runner, scenario sandbox
- chart/ - Chart contract, chart data builder

### Verification (DVH v1.0.0)
- verification/ - Deterministic Verification Harness (run_harness, manifest_validator, input_vector_generator, execution_recorder, replay_engine, bit_comparator, clip_verifier, failure_handler, ci_dvh_gate)

### Integration Tests
- tests/integration/test_full_flow.py - 41 Tests, 2 Szenarien, Determinismus-Verifikation
- tests/integration/test_e2e_fas_pipeline.py - End-to-end FAS pipeline

---

## Entwicklungs-Workflow

### Bei neuer Feature-Implementierung:
1. FAS-Abschnitt lesen (JARVIS_FAS_v6_0_1_Phase6A.txt, relevante .docx Dateien)
2. Import-Regeln pruefen (DAG oben)
3. Determinismus-Garantien einhalten (DET-01 bis DET-07)
4. PROHIBITED-Aktionen vermeiden
5. Kanonische Funktionen importieren, NICHT reimplementieren
6. Tests schreiben BEVOR Implementation (Test-First)
7. pytest ausfuehren -> alle 7513+ Tests muessen gruen sein

### Bei Aenderungen an Stable Core Layern (FREEZE):
Diese duerfen NUR mit:
- Version-Bump (CONTRACT-01)
- Migration-Dokument fuer Konstanten-Aenderungen (CONTRACT-02)
- Backward-compatible Signaturen (CONTRACT-03)
- Audit aller Call-Sites bei Enum-Aenderungen (CONTRACT-04/05)
- Vollstaendigem FAS-Revision bei Arithmetik-Aenderungen (CONTRACT-06)
- Vollstaendigem FAS-Revision bei Clip Chain Aenderungen (CONTRACT-07)

### Delegation-Regel:
Wenn eine Berechnung in einem anderen Modul liegt: IMPORTIEREN und DELEGIEREN.
**Niemals reimplementieren**, auch nicht als Einzeiler.

---

## Wichtige Code-Muster

### Richtig: Kanonische Funktion importieren
```python
# RICHTIG
from jarvis.portfolio.portfolio_allocator import allocate_positions
positions = allocate_positions(total_capital, exposure_fraction, asset_prices)

# FALSCH - Reimplementierung verboten!
allocated = total_capital * exposure_fraction
```

### Richtig: Regime-Vergleich mit Enum
```python
# RICHTIG
from jarvis.core.regime import GlobalRegimeState
if regime == GlobalRegimeState.CRISIS:
    ...

# FALSCH - String-Vergleich verboten!
if regime == "CRISIS":
    ...
```

### Richtig: Fresh Instanz pro Call (DET-02)
```python
# RICHTIG - Fresh per Call
engine = RiskEngine()
result = engine.assess(...)

# FALSCH - Keine gecachten Instanzen!
_cached_engine = RiskEngine()  # Globaler State verboten
```

---

## Verifikation nach Implementierung

Nach jeder neuen Implementierung:
```bash
# 1. Tests laufen lassen
pytest -v

# 2. Coverage pruefen (Ziel: > 80%)
pytest --cov=jarvis --cov-report=term-missing

# 3. DVH laufen lassen (Determinismus pruefen)
python -m jarvis.verification.run_harness \
  --manifest-path jarvis/risk/THRESHOLD_MANIFEST.json \
  --module-version 6.1.0 \
  --runs-dir jarvis/verification/runs

# 4. Quick Import Check
python -c "from jarvis.risk.risk_engine import RiskEngine; print('OK')"
```

---

## Wichtigste FAS-Dokumente

| Datei | Inhalt |
|-------|--------|
| `FAS/JARVIS_FAS_v6_0_1_Phase6A.txt` | Vollstaendige System-FAS (Hauptdokument, 500k+ Zeichen) |
| `FAS/FAS_v6_1_0_Risk_Engine.docx` | Risk Engine Spezifikation (FREEZE) |
| `FAS/DVH_Architecture_Risk_Engine_v6_1_0.docx` | Verification Harness Architektur |
| `FAS/DVH_Implementation_Blueprint_Risk_Engine_v6_1_0.docx` | DVH Implementierungs-Blueprint |
| `FAS/MASTER_FAS_v6_1_0_G_Governance_Integration.docx` | Governance Integration |
| `docs/governance/MASTER_FAS_v6_1_0.docx` | Master FAS |
| `jarvis/ARCHITECTURE.md` | Architektur-Spezifikation (Section 1-10) |

---

*Projekt-Version: MASP v6.2.0 | Harness: 1.0.0 | Tests: 7513 | Status: ALLE MODULE IMPLEMENTIERT*
