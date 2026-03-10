# JARVIS — Multi-Asset Strategy Platform (MASP)
# Decision Quality Platform v6.1.0
# CLAUDE.md — Projektkontext für Claude Code

---

## ⚠️ SYSTEM CLASSIFICATION (P0 — UNVERÄNDERLICH)

**JARVIS ist ein reines Analyse- und Strategie-Forschungsplattform.**
- KEIN Handelssystem. KEIN Broker-API. KEIN Echtgeld-Management.
- Alle Berechnungen operieren auf simulierten Positionen.
- Dieser P0-Status überschreibt alle anderen Layer (P1–P9).
- Jeder Code-Pfad der zu echten Order-Übertragungen führt ist ein kritischer Verstoß.

---

## 📁 Projektstruktur

```
JARVIS/
├── jarvis/
│   ├── core/               ← STABLE CORE (FREEZE – nicht ohne Release ändern!)
│   │   ├── regime.py               GlobalRegimeState, CorrelationRegimeState Enums
│   │   ├── regime_detector.py      RegimeDetector (HMM-basiert)
│   │   ├── state_layer.py          LatentState dataclass
│   │   ├── state_estimator.py      StateEstimator (Kalman-artig)
│   │   ├── volatility_tracker.py   VolatilityTracker (EWMA)
│   │   ├── data_layer.py           Daten-Abstraktion
│   │   ├── feature_layer.py        Feature-Berechnung
│   │   ├── integrity_layer.py      Hash-Chain Validierung
│   │   ├── logging_layer.py        Strukturiertes Logging
│   │   ├── execution_guard.py      Ausführungsschutz
│   │   └── risk_layer/             Risk-Layer Subdomain
│   │       ├── domain.py           RiskDomain Datenmodelle
│   │       ├── engine.py           Risk-Layer Engine
│   │       ├── evaluator.py        Risk Evaluator
│   │       ├── exceptions.py       Risk Exceptions
│   │       └── sizing.py           Position Sizing
│   │
│   ├── risk/               ← STABLE CORE (FREEZE – FAS v6.1.0)
│   │   ├── risk_engine.py          RiskEngine – FREEZE v6.1.0 (HAUPTKOMPONENTE)
│   │   └── THRESHOLD_MANIFEST.json Hash-geschützte Konstanten
│   │
│   ├── utils/              ← STABLE CORE (FREEZE)
│   │   └── constants.py            JOINT_RISK_MULTIPLIER_TABLE + Plattform-Konstanten
│   │
│   ├── portfolio/          ← STABLE CORE (FREEZE)
│   │   └── portfolio_allocator.py  allocate_positions() – KANONISCHE Funktion
│   │
│   ├── execution/          ← STABLE CORE (FREEZE)
│   │   └── exposure_router.py      route_exposure_to_positions() – KANONISCH
│   │
│   ├── governance/         ← Governance Layer
│   │   ├── policy_validator.py     validate_pipeline_config() – GOV-01..GOV-06
│   │   └── exceptions.py           GovernanceViolationError
│   │
│   ├── orchestrator/       ← External Orchestration Layer
│   │   └── pipeline.py             run_full_pipeline() – Haupt-API v1.2.1
│   │
│   ├── backtest/           ← External Layer (implementiert)
│   │   └── engine.py               run_backtest() – Rolling Window Simulation
│   │
│   ├── verification/       ← Deterministic Verification Harness (DVH) v1.0.0
│   │   ├── run_harness.py          Entry Point
│   │   ├── manifest_validator.py   Manifest-Prüfung
│   │   ├── input_vector_generator.py
│   │   ├── execution_recorder.py
│   │   ├── replay_engine.py
│   │   ├── bit_comparator.py
│   │   ├── clip_verifier.py
│   │   ├── failure_handler.py
│   │   ├── data_models/            Dataclasses für DVH
│   │   ├── vectors/                Input Vector Definitionen
│   │   ├── storage/                Record Serialisierung
│   │   └── runs/                   Laufzeit-generierte Verifikations-Records
│   │
│   ├── metrics/            ← External Layer (SCAFFOLD – implementieren!)
│   │   └── engine.py               sharpe_ratio, max_drawdown, calmar_ratio, regime_conditional_returns
│   │
│   ├── strategy/           ← External Layer (SCAFFOLD – implementieren!)
│   │   └── engine.py               momentum_signal, mean_reversion_signal, combine_signals
│   │
│   ├── selection/          ← External Layer (SCAFFOLD – implementieren!)
│   │   └── engine.py               rank_candidates, filter_by_threshold, select_top_n
│   │
│   ├── optimization/       ← External Layer (SCAFFOLD – implementieren!)
│   │   └── engine.py               run_optimization() – Kartesisches Produkt über Parameter
│   │
│   ├── robustness/         ← External Layer (SCAFFOLD – implementieren!)
│   │   └── engine.py               evaluate_robustness()
│   │
│   ├── report/             ← External Layer (SCAFFOLD – implementieren!)
│   │   └── engine.py               generate_report()
│   │
│   └── walkforward/        ← External Layer (SCAFFOLD – implementieren!)
│       └── engine.py               generate_windows, run_walkforward
│
├── tests/                  ← Test Suite (pytest)
│   ├── test_pipeline_contract.py   Haupt-Vertragstest (Pipeline + Backtest)
│   └── unit/
│       ├── core/                   Unit Tests für Core Layer
│       ├── execution/              Unit Tests für Execution Guard
│       ├── governance/             Unit Tests für Policy Validator
│       └── risk_layer/             Unit Tests für Risk Layer
│
├── mutants/                ← Mutation Testing (mutmut) – Spiegelstruktur von tests/
├── FAS/                    ← Formale Architektur-Spezifikation (BAUANLEITUNG)
│   ├── FAS_v6_1_0_Risk_Engine.docx             Risk Engine FAS
│   ├── DVH_Architecture_Risk_Engine_v6_1_0.docx DVH Architektur
│   ├── DVH_Implementation_Blueprint_Risk_Engine_v6_1_0.docx
│   ├── MASTER_FAS_v6_1_0_G_Governance_Integration.docx
│   └── JARVIS_FAS_v6_0_1_Phase6A.txt           Vollständige System-FAS (Hauptdokument)
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

## 🔧 Tech Stack

- **Sprache:** Python 3.10+
- **Kern-Dependencies:** numpy >= 1.24.0, scipy >= 1.10.0
- **Test-Framework:** pytest 9.0.2, pytest-cov
- **Mutation Testing:** mutmut 3.5.0
- **DVH:** Standard Library only (null third-party dependencies)
- **Weitere:** pandas, click, rich, textual, libcst, PyYAML

---

## 🏗️ Architektur-Prinzipien (STRENG EINHALTEN)

### Import-Regeln (gerichteter azyklischer Graph)
```
orchestrator/  → core/, risk/, execution/
backtest/      → core/, orchestrator/
walkforward/   → core/, backtest/, orchestrator/
execution/     → core/, portfolio/
portfolio/     → (nur stdlib)
risk/          → core/, utils/
utils/         → core/
core/          → (nur stdlib)
```

**VERBOTENE Imports:**
- core/, risk/, utils/, portfolio/, execution/ dürfen NIEMALS aus orchestrator/, backtest/, walkforward/ importieren
- Zirkuläre Imports sind absolut verboten

### Determinismus-Garantien (DET-01 bis DET-07)
1. **DET-01** Keine stochastischen Operationen (kein random(), numpy.random, secrets, os.urandom)
2. **DET-02** Kein externer State-Zugriff innerhalb von Berechnungsfunktionen – alle Inputs explizit übergeben
3. **DET-03** Keine Seiteneffekte – Berechnungsfunktionen schreiben nicht in externen State
4. **DET-04** Alle Arithmetik-Operationen sind deterministisch (kein symbolisches Math, kein lazy eval)
5. **DET-05** Alle bedingten Verzweigungen sind deterministische Funktionen expliziter Inputs
6. **DET-06** Fixe Literale als Algorithmus-Parameter werden NICHT parametrisierbar gemacht
7. **DET-07** Rückwärtskompatibilität: Gleiche Inputs = bit-identische Outputs (ohne Version-Bump)

### VERBOTENE Aktionen (absolut, keine Ausnahmen)
| Nr | Verbot |
|----|--------|
| PROHIBITED-01 | Stochastische Operationen (random, Monte Carlo, Sampling) |
| PROHIBITED-02 | File I/O in Berechnungs-Layern (open(), pathlib, csv, json, pickle...) |
| PROHIBITED-03 | Logging in Berechnungs-Layern (logging.getLogger, print(), sys.stderr) |
| PROHIBITED-04 | Environment Variable Zugriff (os.environ, os.getenv, dotenv) |
| PROHIBITED-05 | Globaler mutabler State (module-level mutable containers) |
| PROHIBITED-06 | Reimplementierung kanonischer Logik (immer aus dem kanonischen Owner importieren) |
| PROHIBITED-07 | Änderung von hash-geschützten Konstanten zur Laufzeit |
| PROHIBITED-08 | Neue Regime-Enum-Definitionen außerhalb von jarvis/core/regime.py |
| PROHIBITED-09 | String-basiertes Regime-Branching (immer Enum-Instanzen aus core/regime.py) |
| PROHIBITED-10 | Architektur-Drift (keine neuen Dependency-Edges ohne Review) |

---

## 🚀 Haupt-API

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
# result.exposure_weight    → finale Exposure [0, 1]
# result.risk_regime        → "NORMAL" | "ELEVATED" | "CRITICAL" | "DEFENSIVE"
# result.volatility_forecast → EWMA annualisierte Volatilität
```

### Backtest
```python
from jarvis.backtest.engine import run_backtest
from jarvis.core.regime import GlobalRegimeState

equity_curve = run_backtest(
    returns_series=[...],
    asset_price_series=[...],
    current_regime=GlobalRegimeState.RISK_ON,
    meta_uncertainty=0.2,
    total_capital=100_000.0,
    asset_prices={"SPY": 520.0},
    window=20,
)
```

### Verification Harness
```bash
python -m jarvis.verification.run_harness \
  --manifest-path jarvis/risk/THRESHOLD_MANIFEST.json \
  --module-version 6.1.0 \
  --runs-dir jarvis/verification/runs
```

---

## 📊 Globale Regime-Typen (aus jarvis/core/regime.py)

```python
class GlobalRegimeState(Enum):
    RISK_ON     # Normales Risk-On Umfeld
    RISK_OFF    # Risk-Off Umfeld
    CRISIS      # Krisen-Regime (75% CRISIS-Dampening auf exposure_weight)
    TRANSITION  # Übergangsphase
    UNKNOWN     # Unbekannt
```

---

## 🔒 Hash-Geschützte Konstanten (THRESHOLD_MANIFEST.json)

Diese Konstanten sind hash-geschützt und dürfen NIEMALS ohne Version-Bump und Manifest-Update geändert werden:

| Konstante | Wert | Bedeutung |
|-----------|------|-----------|
| MAX_DRAWDOWN_THRESHOLD | 0.15 | 15% – Hard Limit |
| VOL_COMPRESSION_TRIGGER | 0.30 | 30% ann. Vol → Risk Compression |
| SHOCK_EXPOSURE_CAP | 0.25 | Max 25% Exposure (Clip C Floor) |

**Fixe Literale (FAS DET-06, nicht parametrisierbar):**
- VOL_ADJUSTMENT_CAP = 3.0
- CRISIS_DAMPENING = 0.75
- CLIP_B_FLOOR = 1e-6

---

## 🎯 Clip Chain Order (INV-07 – Reihenfolge darf NICHT geändert werden)

```
E_pre_clip = capital_base × vol_efficiency × uncertainty_penalty × regime_budget
  ↓ Clip A: compute_adaptive_position_size() (position_size_factor)
  ↓ Clip B: np.clip(E_pre_clip, 1e-6, 1.0) [IMMER, bedingungslos]
  ↓ Clip C: np.clip(E/JRM, SHOCK_EXPOSURE_CAP, 1.0) [nur wenn JRM aktiv]
  ↓ CRISIS Dampening: × 0.75 [nur wenn CRISIS Regime]
  = exposure_weight (Output)
```

---

## 🧪 Tests ausführen

```bash
# Alle Tests
pytest

# Mit Coverage
pytest --cov=jarvis --cov-report=term-missing

# Einzelner Test
pytest tests/test_pipeline_contract.py -v

# Mutation Tests (dauert länger)
cd mutants && mutmut run

# CI Check Script
python scripts/run_ci_checks.py
```

---

## 📋 Governance Rules (GOV-01 bis GOV-06)

| Regel | Feld | Constraint |
|-------|------|-----------|
| GOV-01 | meta_uncertainty | Muss in [0.0, 1.0] liegen |
| GOV-02 | initial_capital | Muss strikt positiv (> 0.0) sein |
| GOV-03 | window | Muss Integer und >= 20 sein |
| GOV-04 | step | Muss Integer und >= 1, <= window sein |
| GOV-05 | regime | Muss GlobalRegimeState Instanz sein |
| GOV-06 | CRISIS + meta | CRISIS ist valides Regime; meta=0.1 ist legitim |

---

## 📌 Was bereits vollständig implementiert ist (FREEZE)

- ✅ `jarvis/core/regime.py` – Regime Enums
- ✅ `jarvis/core/regime_detector.py` – HMM-basierter Regime Detector
- ✅ `jarvis/core/state_layer.py` – LatentState
- ✅ `jarvis/core/state_estimator.py` – StateEstimator
- ✅ `jarvis/core/volatility_tracker.py` – EWMA Volatility Tracker
- ✅ `jarvis/core/data_layer.py` – Data Abstraction Layer
- ✅ `jarvis/core/feature_layer.py` – Feature Layer
- ✅ `jarvis/core/integrity_layer.py` – Hash-Chain Validierung
- ✅ `jarvis/core/risk_layer/` – Risk Layer Subdomain (domain, engine, evaluator, exceptions, sizing)
- ✅ `jarvis/risk/risk_engine.py` – RiskEngine v6.1.0 (FREEZE)
- ✅ `jarvis/utils/constants.py` – Alle hash-geschützten Konstanten
- ✅ `jarvis/portfolio/portfolio_allocator.py` – allocate_positions()
- ✅ `jarvis/execution/exposure_router.py` – route_exposure_to_positions()
- ✅ `jarvis/governance/policy_validator.py` – validate_pipeline_config()
- ✅ `jarvis/orchestrator/pipeline.py` – run_full_pipeline() v1.2.1
- ✅ `jarvis/backtest/engine.py` – run_backtest()
- ✅ `jarvis/verification/` – Deterministic Verification Harness v1.0.0
- ✅ `tests/` – Vollständige Test-Suite (Pipeline Contract + Unit Tests)

---

## 🚧 Was noch implementiert werden muss (gemäß FAS)

### Sofort (SCAFFOLDS → vollständig implementieren)
- 🔲 `jarvis/metrics/engine.py` – sharpe_ratio, max_drawdown, calmar_ratio, regime_conditional_returns
- 🔲 `jarvis/strategy/engine.py` – momentum_signal, mean_reversion_signal, combine_signals + run_strategy()
- 🔲 `jarvis/selection/engine.py` – rank_candidates, filter_by_threshold, select_top_n + run_selection()
- 🔲 `jarvis/walkforward/engine.py` – generate_windows(), run_walkforward() (vollständig)
- 🔲 `jarvis/optimization/engine.py` – run_optimization() (Kartesisches Produkt)
- 🔲 `jarvis/robustness/engine.py` – evaluate_robustness()
- 🔲 `jarvis/report/engine.py` – generate_report() (konsumiert compute_metrics())

### Phase 3 – Decision Quality (aus FAS v6.0.1)
- 🔲 `jarvis/intelligence/decision_quality_engine.py` – DecisionQualityEngine (< 20ms/cycle)
- 🔲 `jarvis/confidence/adaptive_selectivity_model.py` – AdaptiveSelectivityModel
- 🔲 `jarvis/intelligence/regime_duration_model.py` – RegimeDurationModel
- 🔲 `jarvis/strategy/signal_fragility_analyzer.py` – SignalFragilityAnalyzer (< 30ms/eval)
- 🔲 `jarvis/core/decision_context_state.py` – DecisionContextState (frozen dataclass)
- 🔲 `jarvis/core/system_mode.py` – SystemMode Enum + GlobalSystemStateController

### System Modi (aus FAS)
- 🔲 MODE_HISTORICAL – Static historical dataset, batch recompute
- 🔲 MODE_LIVE_ANALYTICAL – Live data stream (read-only), incremental updates
- 🔲 MODE_HYBRID – Historical backfill + live incremental

### Tests ergänzen
- 🔲 Unit Tests für alle Scaffold-Module nach Implementierung
- 🔲 Integration Tests für vollständige Pipeline (metrics → strategy → selection → optimization → report)

---

## ⚙️ Entwicklungs-Workflow

### Bei neuer Feature-Implementierung (Scaffolds):
1. FAS-Abschnitt lesen (JARVIS_FAS_v6_0_1_Phase6A.txt, relevante .docx Dateien)
2. Import-Regeln prüfen (Section 2 in ARCHITECTURE.md)
3. Determinismus-Garantien einhalten (DET-01 bis DET-07)
4. PROHIBITED-Aktionen vermeiden
5. Kanonische Funktionen importieren, NICHT reimplementieren
6. Tests schreiben BEVOR Implementation (Test-First)
7. pytest ausführen → alle Tests müssen grün sein

### Bei Änderungen an Stable Core Layern (FREEZE):
⚠️ Diese dürfen NUR mit:
- Version-Bump (CONTRACT-01)
- Migration-Dokument für Konstanten-Änderungen (CONTRACT-02)
- Backward-compatible Signaturen (CONTRACT-03)
- Audit aller Call-Sites bei Enum-Änderungen (CONTRACT-04/05)
- Vollständigem FAS-Revision bei Arithmetik-Änderungen (CONTRACT-06)
- Vollständigem FAS-Revision bei Clip Chain Änderungen (CONTRACT-07)

### Delegation-Regel:
Wenn eine Berechnung in einem anderen Modul liegt: IMPORTIEREN und DELEGIEREN.
**Niemals reimplementieren**, auch nicht als Einzeiler.

---

## 🔑 Wichtige Code-Muster

### Richtig: Kanonische Funktion importieren
```python
# ✅ RICHTIG
from jarvis.portfolio.portfolio_allocator import allocate_positions
positions = allocate_positions(total_capital, exposure_fraction, asset_prices)

# ❌ FALSCH – Reimplementierung verboten!
allocated = total_capital * exposure_fraction
```

### Richtig: Regime-Vergleich mit Enum
```python
# ✅ RICHTIG
from jarvis.core.regime import GlobalRegimeState
if regime == GlobalRegimeState.CRISIS:
    ...

# ❌ FALSCH – String-Vergleich verboten!
if regime == "CRISIS":
    ...
```

### Richtig: Fresh Instanz pro Call (DET-02)
```python
# ✅ RICHTIG – Fresh per Call
engine = RiskEngine()
result = engine.assess(...)

# ❌ FALSCH – Keine gecachten Instanzen!
_cached_engine = RiskEngine()  # Globaler State verboten
```

---

## 📞 Verifikation nach Implementierung

Nach jeder neuen Implementierung:
```bash
# 1. Tests laufen lassen
pytest -v

# 2. Coverage prüfen (Ziel: > 80%)
pytest --cov=jarvis --cov-report=term-missing

# 3. DVH laufen lassen (Determinismus prüfen)
python -m jarvis.verification.run_harness \
  --manifest-path jarvis/risk/THRESHOLD_MANIFEST.json \
  --module-version 6.1.0 \
  --runs-dir jarvis/verification/runs

# 4. Quick Import Check
python -c "from jarvis.risk.risk_engine import RiskEngine; print('OK')"
```

---

## 📖 Wichtigste FAS-Dokumente

| Datei | Inhalt |
|-------|--------|
| `FAS/JARVIS_FAS_v6_0_1_Phase6A.txt` | Vollständige System-FAS (Hauptdokument, 500k+ Zeichen) |
| `FAS/FAS_v6_1_0_Risk_Engine.docx` | Risk Engine Spezifikation (FREEZE) |
| `FAS/DVH_Architecture_Risk_Engine_v6_1_0.docx` | Verification Harness Architektur |
| `FAS/DVH_Implementation_Blueprint_Risk_Engine_v6_1_0.docx` | DVH Implementierungs-Blueprint |
| `FAS/MASTER_FAS_v6_1_0_G_Governance_Integration.docx` | Governance Integration |
| `docs/governance/MASTER_FAS_v6_1_0.docx` | Master FAS |
| `jarvis/ARCHITECTURE.md` | Architektur-Spezifikation (Section 1-10) |

---

*CLAUDE.md generiert basierend auf vollständiger Analyse der ZIP + FAS-Dokumente*
*Projekt-Version: MASP v6.1.0 | Harness: 1.0.0 | Status: FREEZE (Core) / ACTIVE DEVELOPMENT (Scaffolds)*
