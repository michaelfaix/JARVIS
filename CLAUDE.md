# JARVIS — CLAUDE.md
## AI Trading Intelligence Platform
**Version:** 7.0.0 (Backend FINAL) | **Stand:** März 2026 | **Autor:** Michael Faix

---

## 🎯 GESAMTVISION

JARVIS ist eine **AI-gestützte Trading-Intelligence-Plattform** mit zwei Schichten:

```
JARVIS-Trader (Frontend SaaS)          ← NÄCHSTER SCHRITT
    ↓
JARVIS Backend (Python Engine)         ← 100% FERTIG ✅
```

**Langfristige Vision** (analog TradingView + Revolut):
- AI Market Intelligence & Trading Signals
- Portfolio Tracking & Risk Guardian
- Strategy Builder & Marketplace
- Community & Social Trading
- Paper Trading → später echtes Trading
- Crypto Wallet & Fintech App

---

## 🏆 BACKEND — FINAL ABGESCHLOSSEN

> ⚠️ Das Backend ist vollständig. FAS-Datei wird NICHT mehr aktualisiert.
> Keine weiteren Backend-Sprints nötig. Fokus ab jetzt: **JARVIS-Trader Frontend**.

| Metrik | Wert |
|--------|------|
| **Tests** | **8.890** ✅ |
| **FAS-Compliance** | **100% (876/876)** 🏆 |
| **S01-S05 Core** | **97%** ✅ |
| **S06-S15 ML+Systems** | **100%** ✅ |
| **S26-S37 Strategy+Gov** | **100%** ✅ |
| **Multi-Asset** | **98%** ✅ |
| **Coverage** | **96%+** ✅ |
| **Mutation Kill-Rate** | **~95%** ✅ |
| **DVH** | **PASS** ✅ |
| **Warnings** | **0** ✅ |
| **Performance** | **0.76ms** P95 🚀 |

### Implementierte ML-Module (S06-S15)
| Modul | Datei | Tests |
|-------|-------|-------|
| S06 FastPath | `jarvis/models/fast_path.py` | 105 |
| S07 DeepPath | `jarvis/models/deep_path.py` | 100 |
| S08 Uncertainty | `jarvis/models/uncertainty.py` | 94 |
| S09 Calibration | `jarvis/models/calibration.py` | 39 |
| S09.5 AutoRecalibrator | `jarvis/models/auto_recalibrator.py` | 31 |
| S10 OOD Detection | `jarvis/models/ood_detection.py` | 78 |
| S11 Quality Scorer | `jarvis/systems/quality_scorer.py` | 63 |
| S12 Learning Engine | `jarvis/systems/learning_engine.py` | 55 |
| S13 Degradation Ctrl | `jarvis/systems/degradation_ctrl.py` | 62 |
| S14 API Layer | `jarvis/api/{routes,models,ws}.py` | 66 |
| S15 Validation | `jarvis/validation/{validators,stress,metrics}.py` | 113 |

---

## 🏗️ BACKEND-ARCHITEKTUR

```
Tier 1 — Core Infrastructure      event_log, state_controller, market_data_provider...
Tier 2 — Intelligence Stack       regime_transition, bayesian_confidence...
Tier 3 — Confidence & Risk        failure_impact, stress_detector...
Tier 4 — Governance & Control     control_flow, mode_controller, reproducibility...
Tier 5 — Research & Validation    walk_forward_validation, overfitting_detector...
Tier 6 — Metrics & Observability  fragility_index, trust_score, governance_monitor...
MA     — Multi-Asset              global_regime, asset_regimes, correlation_regime...
ML     — S06-S15 Model Layer      fast_path, deep_path, uncertainty, calibration...
API    — S14 FastAPI              /health /predict /feedback /status /metrics + WebSocket
VAL    — S15 Validation           validators, stress (15 Szenarien), metrics (8 VETO)
```

**Import-Regel:** Nur Top→Down. Kein numpy in Intelligence Layer (DVH).

### S14 API-Endpunkte (Frontend verbindet sich hier)
| Endpoint | Methode | Beschreibung |
|----------|---------|-------------|
| `/health` | GET | System-Status |
| `/predict` | POST | JARVIS Signal für Asset |
| `/feedback` | POST | User-Feedback |
| `/status` | GET | System-Modus, Metriken |
| `/metrics` | GET | Quality Score, Trust Score |
| `/stream/{symbol}` | WebSocket | Live Signal-Stream |

---

## 🖥️ FRONTEND: JARVIS-Trader

### Tech Stack
| Komponente | Technologie | Kosten |
|------------|-------------|--------|
| Web Framework | Next.js 14 + React + TypeScript | €0 |
| Charts | TradingView Lightweight Charts v4 | €0 |
| Styling | Tailwind CSS + shadcn/ui | €0 |
| Mobile | Capacitor.js (PWA → App Store) | €0 |
| Database + Auth | Supabase (PostgreSQL + JWT + Social Login) | €0 |
| Hosting | Railway.app | €5/Mo |
| Payments | Stripe (Subscriptions, SEPA) | % pro Transaktion |
| Crypto Live-Daten | Binance WebSocket | €0 |
| Forex/Stock-Daten | Alpha Vantage | €0 → €50/Mo |
| Monitoring | Sentry + Grafana Cloud | €0 |
| **MVP GESAMT** | | **~€159 einmalig** |

> ⚠️ NICHT für MVP: AWS, Kubernetes, Kafka — Railway + Supabase reicht bis 10.000+ User.

### Kernfunktionen
- **Dashboard:** Market Regime, Top Opportunities, Latest Signals, Portfolio Risk
- **Charts:** Candlestick + Signal Marker + Entry/Exit + Regime Overlay + Multi-TF
- **Signals Feed:** Asset, Direction, Entry, Stop Loss, TP, Confidence Score
- **Opportunity Radar:** Top-Opportunities nach Trend-Stärke, Volumen, Momentum
- **Portfolio Intelligence:** Asset Allocation, P&L, Risk Score, Diversification
- **Risk Guardian:** Position Size Check, Drawdown Warning, Correlation Check
- **Paper Trading:** Market/Limit/SL/TP Orders, PnL, Win Rate, Drawdown
- **AI Chat:** Marktfragen → JARVIS + Claude API antwortet
- **Strategy Lab:** Eigene Strategien bauen, Backtesting, Sharing
- **Community:** Leaderboards, Top Traders, Strategy Marketplace

### Tier-Modell
| Feature | 🆓 Free | ⭐ Pro (€29/Mo) | 🏢 Enterprise (€199/Mo) |
|---------|---------|----------------|------------------------|
| Charts | 3 Assets, 2 TF | Alle | Alle + Custom Feeds |
| Strategien | 1 (Scalping) | 8 Strategien | Alle + eigene |
| Paper Trading | €10.000 | €1k–€500k | Unbegrenzt |
| JARVIS-Signale | 15 Min verzögert | Echtzeit | Echtzeit + Rohdaten |
| Regime-Detection | Basis | Vollständig (3-Tier) | Vollständig + Config |
| OOD-Warnungen | ❌ | ✅ | ✅ + Schwellwerte |
| Backtesting | ❌ | 90 Tage + WFV | Unbegrenzt |
| AI Chat | ❌ | ✅ | ✅ + Priorität |
| API-Zugang | ❌ | ❌ | ✅ REST + WebSocket |
| Support | Community | E-Mail (48h) | Priority Slack (4h) |

### USP — Zeitfenster-Regler
> Nutzer zieht Slider 1m → 1W → JARVIS wählt automatisch optimale Strategie
> + berechnet Entry/Exit neu + Regime-Detection passt sich an.
> Kein Konkurrent bietet das.

---

## 🗺️ FRONTEND ENTWICKLUNGSPLAN

```
Phase 0  Landing Page + Warteliste          3 Tage     ← JETZT STARTEN
Phase 1  Next.js → JARVIS API verbinden     3 Wochen   (S14 ist fertig!)
Phase 2  Auth (Supabase) + Stripe           2 Wochen
Phase 3  Charts + Signale + Radar           4 Wochen
Phase 4  Paper Trading + Dashboard          3 Wochen
Phase 5  PWA + Mobile (Capacitor)           2 Wochen
Phase 6  Stripe Free/Pro/Enterprise         1 Woche
Phase 7  Beta Launch (50-100 User)          2 Wochen
──────────────────────────────────────────────────────
GESAMT   ~17 Wochen (4 Monate)
```

### Produkt-Roadmap
| Version | Zeitraum | Features |
|---------|----------|---------|
| v0.1 MVP | Monat 1-4 | Charts, Paper Trading, Signale, Free/Pro |
| v0.2 Beta | Monat 5 | Community, Trade-Journal, Gamification |
| v1.0 | Monat 6 | Enterprise, API, Mobile Apps im Store |
| v1.1 | Monat 7-8 | Social Trading: Top-Trader folgen |
| v1.2 | Monat 9-10 | Strategy Marketplace |
| v1.3 | Monat 11-12 | Broker-Integration (read-only) |
| v2.0 | Jahr 2 | AI-Coach: personalisierter Lernpfad |

---

## 📦 MARKTDATEN

| Provider | Märkte | Kosten | Status |
|----------|--------|--------|--------|
| Binance WebSocket | Crypto (500+ Paare) | €0 | ✅ Sofort |
| FRED API | Macro, Rates | €0 | ✅ Sofort |
| Alpha Vantage | Forex, Stocks, Commodities | €0 (25 req/Tag) | MVP |
| Twelve Data | Forex, Crypto | €0 (800 req/Tag) | Fallback |
| Polygon.io | US Stocks Echtzeit | $29/Mo | Phase 2 |

---

## 💰 FINANZPLANUNG

| Posten | Kosten |
|--------|--------|
| Domain (jarvis-trader.app) | €15/Jahr |
| Apple Developer Account | €99/Jahr |
| Google Play Account | €25 einmalig |
| Server, DB, APIs | €0 (Free Tiers) |
| **MVP GESAMT** | **~€159** |

**Break-Even: ~150 Pro-User = €4.350/Mo**

| Zeitraum | ARR (realistisch) |
|----------|-------------------|
| Monat 12 | €50k–€120k |
| Monat 24 | €300k–€800k |

---

## 🔒 SICHERHEIT & RECHTLICHES

- Auth: Supabase JWT + Google/Apple SSO + 2FA
- Transport: TLS 1.3 (Cloudflare), DDoS-Schutz kostenlos
- Rate Limiting: FastAPI Middleware (bereits in S14)

### Pflicht-Dokumente vor Launch
- [ ] AGB / Terms of Service
- [ ] Datenschutzerklärung (DSGVO)
- [ ] Disclaimer: "Kein Anlageberater, Paper Trading = Simulation"
- [ ] Cookie-Richtlinie + Impressum
- [ ] Subscription-AGB (Stripe)

---

## 💻 BEFEHLE

```powershell
# Tests
python -m pytest --tb=short -q

# Coverage
COVERAGE_FILE=/tmp/.coverage python -m pytest --cov=jarvis --cov-report=term-missing -q

# DVH
python -m jarvis.verification.run_harness --manifest-path jarvis/risk/THRESHOLD_MANIFEST.json --module-version 6.1.0 --runs-dir jarvis/verification/runs

# Git
git add -A && git commit -m "message" && git push origin master

# Windows Permissions (Admin PowerShell)
takeown /F "C:\Project\JARVIS" /R /D J
icacls "C:\Project\JARVIS" /grant DESKTOP-PQU68JS\MikeFaix:F /T
```

---

## ⚙️ BEKANNTE WORKAROUNDS

| Problem | Lösung |
|---------|--------|
| Coverage Permission Error | `COVERAGE_FILE=/tmp/.coverage python -m pytest ...` |
| Git Line Endings | `.gitattributes`: LF für Python, CRLF für .bat/.cmd |
| numpy in Intelligence Layer | Verboten (DVH) — stdlib-only |
| `datetime.utcnow()` | `datetime.now(timezone.utc)` |

---

## 📂 WICHTIGE DATEIEN

| Datei | Inhalt |
|-------|--------|
| `CLAUDE.md` | Diese Datei |
| `README.md` | Öffentliche Projektdoku |
| `IMPLEMENTATION_STATUS.md` | FAS-Compliance (100% — abgeschlossen, nicht mehr updaten) |
| `FAS/FAS_frontend.txt` | Frontend-Spezifikation (JARVIS-Trader) |
| `jarvis/api/main.py` | FastAPI App Entry Point (CORS, Router Mount) |
| `jarvis/api/routes.py` | FastAPI Endpoints — Frontend verbindet sich hier |
| `jarvis/api/ws.py` | WebSocket Live-Stream |
| `jarvis/validation/` | S15 Validation Layer |
| `jarvis/verification/` | DVH-Harness + Runs |
| `jarvis/risk/THRESHOLD_MANIFEST.json` | Hash-geschützte Schwellwerte |

---

## ✅ ABGESCHLOSSEN: FastAPI Entry Point

- `jarvis/api/main.py` erstellt — CORS für localhost:3000, Router unter /api/v1
- 8897 Tests grün (inkl. 7 neue main.py Tests)
- Frontend erstellt: Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui

---

## ✅ ABGESCHLOSSEN: Frontend Dashboard v1

### Erstellt:
- `frontend/` — Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui
- Dashboard mit Market Regime Anzeige (5 Regime-States, farbcodiert)
- BTC/USD Chart mit TradingView Lightweight Charts + JARVIS Signal Overlay
- System Status Cards (Degradation Mode, Quality Score, Connection)
- API Client verbunden mit `localhost:8000/api/v1`
- Build erfolgreich (`npx next build` → 0 Errors)
- 8897 Backend-Tests grün

---

## ✅ ABGESCHLOSSEN: Frontend Navigation + 6 Seiten

### Erstellt:
- Sidebar Navigation mit Icons (lucide-react): Dashboard, Signals, Portfolio, Radar, Strategy Lab, Settings
- **Signals-Seite**: Live Signal Feed (8 Assets), Direction Badges, Entry/SL/TP, Confidence Bars, Quality Score, OOD Warning
- **Portfolio-Seite**: Paper Trading Konto, Asset Allocation, P&L, Risk Score, Open Positions mit Close-Button
- **Opportunity Radar**: Top Opportunities, Tabs (All/Long/Short/Top), Momentum Scanner
- **Strategy Lab**: 3 Strategien (Momentum, Mean Reversion, Combined), Backtest Panel (Coming Soon)
- **Settings**: Paper Capital, Strategy-Wahl, Asset Tracking, Dark/Light Theme, Poll Interval, Reset
- 11 shadcn/ui Komponenten (Card, Badge, Button, Table, Input, Label, Select, Separator, Tabs, Progress, Switch)
- 7 Custom Hooks (use-jarvis, use-signals, use-portfolio, use-settings, use-sidebar, use-prices)
- Route Group `(app)/` mit shared Sidebar Layout
- Build: 0 Errors, 6 Routes | Backend: 8897 Tests grün

---

## ✅ ABGESCHLOSSEN: Paper Trading Engine + Live Prices

### Erstellt:
- **Paper Trading Accept/Close**: Accept-Button auf Signals-Seite öffnet Trade (10% des verfügbaren Kapitals), Close-Button schließt Position
- **Live Binance Preise**: `use-prices.ts` Hook holt BTC, ETH, SOL Preise von Binance REST API (kostenlos, kein API-Key)
- **Synthetic Fallback**: Nicht-Crypto Assets (SPY, AAPL, etc.) nutzen synthetische Random-Walk-Preise
- **Portfolio Real-Time P&L**: Portfolio-Seite aktualisiert Positionen automatisch mit Live-Preisen alle 5s
- **Binance Status Indicator**: Wifi-Icon zeigt ob Live- oder Synthetic-Preise aktiv sind
- Signals-Seite: Live Price Spalte, Open Trades Counter, Available Capital Anzeige
- Build: 0 Errors, 6 Routes | Backend: 8897 Tests grün

---

## 🔜 NÄCHSTER SCHRITT

### Sofort (ohne Code, diese Woche):
1. Domain: **jarvis-trader.app** registrieren (~€15)
2. **Supabase** Account: supabase.com (kostenlos)
3. **Railway** Account: railway.app (kostenlos)
4. **Stripe** Account: stripe.com
5. **Landing Page** + Warteliste: Framer.com

### Erster Claude Code Befehl für Frontend:
```
Erstelle ein neues Next.js 14 Projekt für JARVIS-Trader.
Verbinde es mit dem JARVIS Backend über jarvis/api/routes.py (FastAPI).
Implementiere zuerst: Dashboard mit Market Regime Anzeige +
BTC/USD Chart mit TradingView Lightweight Charts + JARVIS Signal Overlay.
```

---

*CLAUDE.md — Version 7.3.0 | März 2026*
*Backend 100% FAS-konform und abgeschlossen. FAS-Datei wird nicht mehr aktualisiert.*
