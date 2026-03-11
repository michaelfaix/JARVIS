# JARVIS — CLAUDE.md
## AI Trading Intelligence Platform
**Version:** 6.2.0 (Backend) | **Stand:** März 2026 | **Autor:** Michael Faix

---

## 🎯 GESAMTVISION

JARVIS ist eine **AI-gestützte Trading-Intelligence-Plattform** mit zwei Schichten:

```
JARVIS-Trader (Frontend SaaS)          ← Wird gebaut
    ↓
JARVIS Backend (Python Engine)         ← Fertig ✅
```

**Langfristige Vision** (analog TradingView + Revolut):
- AI Market Intelligence
- Trading Signals & Analysis
- Portfolio Tracking & Risk Guardian
- Strategy Builder & Marketplace
- Community & Social Trading
- Paper Trading → später echtes Trading
- Crypto Wallet & Fintech App

---

## 📊 AKTUELLER BACKEND-STAND (März 2026)

| Metrik | Wert |
|--------|------|
| **Tests** | **8.127** ✅ |
| **FAS-Compliance Overall** | **91%** (801/876) |
| **Core Platform** | **98%** ✅ |
| **Multi-Asset** | **98%** ✅ |
| **S26-S37 Strategy/Gov** | **100%** ✅ |
| **S06-S15 ML-Layer** | **42%** (Sprint 1 fertig) |
| **Coverage (produktiv)** | **96%+** ✅ |
| **Mutation Kill-Rate** | **~95%** ✅ |
| **DVH** | **PASS** ✅ |
| **Warnings** | **0** ✅ |
| **Performance** | **0.76ms** P95 🚀 |

### ML-Layer Sprint-Status
| Sprint | Module | Status |
|--------|--------|--------|
| Sprint 1 | S06 FastPath + S07 DeepPath | ✅ Fertig |
| Sprint 2 | S08 Uncertainty + S09 Calibration + S09.5 AutoRecalibrator | ⏳ Läuft |
| Sprint 3 | S10 OOD Detection + S11 Quality Scorer | 🔜 |
| Sprint 4 | S12 Learning Engine + S13 Degradation Control | 🔜 |
| Sprint 5 | S14 API Layer + S15 Validation | 🔜 |

---

## 🏗️ BACKEND-ARCHITEKTUR (Fertig)

```
Tier 1 — Core Infrastructure      event_log, state_controller, market_data_provider...
Tier 2 — Intelligence Stack       regime_transition, bayesian_confidence, epistemic_uncertainty...
Tier 3 — Confidence & Risk        failure_impact, stress_detector...
Tier 4 — Governance & Control     control_flow, mode_controller, reproducibility...
Tier 5 — Research & Validation    walk_forward_validation, overfitting_detector...
Tier 6 — Metrics & Observability  fragility_index, trust_score, governance_monitor...
MA     — Multi-Asset Extension    global_regime, asset_regimes, correlation_regime...
ML     — S06-S15 Model Layer      fast_path ✅, deep_path ✅, uncertainty ⏳...
```

**Import-Regel:** Nur Top→Down. Kein numpy in Intelligence Layer (DVH).

---

## 🖥️ FRONTEND TECH STACK (Wird gebaut)

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
| E-Mail | Resend.com | €0 |
| **MVP GESAMT** | | **~€159 einmalig** |

> ⚠️ NICHT für MVP: AWS, Kubernetes, Kafka — überdimensioniert und teuer.
> Railway + Supabase reicht bis 10.000+ User.

---

## 🛍️ PRODUKT: JARVIS-Trader

### Kernfunktionen (FAS_frontend.txt)
- **Dashboard:** Market Regime, Top Opportunities, Latest Signals, Portfolio Risk
- **Charts:** Candlestick + Signal Marker + Entry/Exit + Regime Overlay + Multi-Timeframe
- **Signals Feed:** Asset, Direction, Entry, Stop Loss, TP, Confidence Score
- **Opportunity Radar:** Top-Opportunities nach Trend-Stärke, Volumen, Momentum
- **Portfolio Intelligence:** Asset Allocation, P&L, Risk Score, Diversification
- **Risk Guardian:** Position Size Check, Drawdown Warning, Correlation Check
- **Paper Trading:** Market/Limit/SL/TP Orders, PnL, Win Rate, Drawdown
- **AI Assistant (Chat):** Marktfragen → JARVIS analysiert + antwortet (Claude API)
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

### 8 Trading-Strategien
1. **Scalping** (1m, 5m) — Free
2. **Day Trading** (15m, 1H) — Pro
3. **Swing Trading** (4H, 1D) — Pro
4. **Momentum** (1H, 4H) — Pro
5. **Mean Reversion** (15m, 1H) — Pro
6. **Regime-Adaptive** (Auto) — Pro
7. **RSI Divergence** (1H, 4H) — Pro
8. **VWAP Anchored** (5m, 15m) — Pro

### USP — Zeitfenster-Regler
> Nutzer zieht Slider 1m → 1W → JARVIS wählt automatisch optimale Strategie
> + berechnet Entry/Exit neu + Regime-Detection passt sich an.
> Kein Konkurrent bietet das.

---

## 🗺️ ENTWICKLUNGSREIHENFOLGE

### Backend ML-Layer (läuft gerade in Claude Code)
```
Sprint 1: S06 FastPath + S07 DeepPath          ✅ Fertig (8127 Tests)
Sprint 2: S08 Uncertainty + S09 Cal + S09.5    ⏳ Läuft
Sprint 3: S10 OOD + S11 Quality Scorer         🔜
Sprint 4: S12 Learning + S13 Degradation       🔜
Sprint 5: S14 API Layer + S15 Validation       🔜  ← Brücke zum Frontend!
```

### Frontend Phasen (nach ML-Layer)
```
Phase 0  Landing Page + Warteliste      3 Tage
Phase 1  FastAPI S14 + WebSocket        3 Wochen
Phase 2  Auth + DB + Stripe             2 Wochen
Phase 3  Charts + Signale + Radar       4 Wochen
Phase 4  Paper Trading + Dashboard      3 Wochen
Phase 5  PWA + Mobile (Capacitor)       2 Wochen
Phase 6  Stripe Payments                1 Woche
Phase 7  Beta Launch (50-100 User)      2 Wochen
─────────────────────────────────────────────────
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

### MVP-Kosten: ~€159 einmalig
| Posten | Kosten |
|--------|--------|
| Domain (jarvis-trader.app) | €15/Jahr |
| Apple Developer Account | €99/Jahr |
| Google Play Account | €25 einmalig |
| Server, DB, APIs | €0 (Free Tiers) |

### Break-Even: ~150 Pro-User = €4.350/Mo
### Revenue-Ziele
- Monat 12: €50k–€120k ARR (konservativ–realistisch)
- Monat 24: €300k–€800k ARR

---

## 🔒 SICHERHEIT & RECHTLICHES

### Security-Stack
- Auth: Supabase JWT + Google/Apple SSO + 2FA
- Transport: TLS 1.3 via Cloudflare
- DDoS: Cloudflare Free
- Rate Limiting: FastAPI Middleware
- Verschlüsselung: AES-256 (Supabase)

### Pflicht-Dokumente (vor Launch)
- [ ] AGB / Terms of Service
- [ ] Datenschutzerklärung (DSGVO)
- [ ] Disclaimer: "Kein Anlageberater, keine Garantien, Paper Trading = Simulation"
- [ ] Cookie-Richtlinie
- [ ] Impressum (österreichisches Recht)
- [ ] Subscription-AGB (Stripe Widerruf etc.)

> Anwalt für AGB empfohlen: ~€500 einmalig

---

## 💻 BEFEHLE

```powershell
# Alle Tests
python -m pytest --tb=short -q

# Mit Coverage
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
| `datetime.utcnow()` deprecated | `datetime.now(timezone.utc)` |

---

## 📂 WICHTIGE DATEIEN

| Datei | Inhalt |
|-------|--------|
| `CLAUDE.md` | Diese Datei |
| `README.md` | Öffentliche Projektdoku |
| `IMPLEMENTATION_STATUS.md` | FAS-Compliance-Tracking |
| `FAS/JARVIS_FAS_v6_0_1_Phase6A...` | Vollständige Spezifikation |
| `FAS/FAS_frontend.txt` | Frontend-Spezifikation (JARVIS-Trader) |
| `jarvis/verification/` | DVH-Harness + Runs |
| `jarvis/risk/THRESHOLD_MANIFEST.json` | Hash-geschützte Schwellwerte |
| `.gitattributes` | LF-Enforcement |
| `.gitignore` | incl. `FAS/*API*Key*`, `.coverage*` |

---

## 🔜 NÄCHSTE SCHRITTE

### Jetzt (Claude Code) — Sprint 2:
```
Starte Sprint 2: Implementiere S08 Uncertainty Layer (jarvis/models/uncertainty.py),
S09 Calibration Extension (calibration.py erweitern) und
S09.5 AutoRecalibrator (jarvis/models/auto_recalibrator.py)
sequentiell nach FAS. Mit allen Tests.
Nach Abschluss: pytest full suite + IMPLEMENTATION_STATUS.md aktualisieren.
```

### Nach ML-Layer abgeschlossen — S14 Frontend-Brücke:
```
Implementiere jarvis/api/routes.py, jarvis/api/models.py und jarvis/api/ws.py
als FastAPI-Layer über JARVIS nach FAS S14 mit allen Tests.
```

### Sofort-Aktionen (parallel, ohne Code):
1. Domain registrieren: jarvis-trader.app (~€15)
2. Supabase Account erstellen: supabase.com (kostenlos)
3. Railway Account: railway.app (kostenlos)
4. Stripe Account: stripe.com
5. Landing Page: Framer.com + Warteliste

---

*CLAUDE.md zuletzt aktualisiert: März 2026 | JARVIS v6.2.0 + JARVIS-Trader Vision*
*Quellen: FAS v6.0.1, FAS_frontend.txt, ChatGPT Masterplan, Session-Protokoll*
