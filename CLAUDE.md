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
- Build: 0 Errors, 7 Routes | Backend: 8897 Tests grün

---

## ✅ ABGESCHLOSSEN: Paper Trading Engine + Live Prices

### Erstellt:
- **Paper Trading Accept/Close**: Accept-Button auf Signals-Seite öffnet Trade (10% des verfügbaren Kapitals), Close-Button schließt Position
- **Live Binance Preise**: `use-prices.ts` Hook holt BTC, ETH, SOL Preise von Binance REST API (kostenlos, kein API-Key)
- **Synthetic Fallback**: Nicht-Crypto Assets (SPY, AAPL, etc.) nutzen synthetische Random-Walk-Preise
- **Portfolio Real-Time P&L**: Portfolio-Seite aktualisiert Positionen automatisch mit Live-Preisen alle 5s
- **Binance Status Indicator**: Wifi-Icon zeigt ob Live- oder Synthetic-Preise aktiv sind
- Signals-Seite: Live Price Spalte, Open Trades Counter, Available Capital Anzeige
- Build: 0 Errors, 7 Routes | Backend: 8897 Tests grün

---

## ✅ ABGESCHLOSSEN: Risk Guardian + Trade History + Dashboard Enhancement

### Erstellt:
- **Risk Guardian Seite** (`/risk`): 4 automatische Risk-Checks (Single Asset Exposure, Portfolio Drawdown, Open Positions, Cash Reserve), Farbcodierung (PASS/WARN/FAIL), Asset Exposure Breakdown, Trading Performance Stats
- **Trade History**: Closed Trades werden gespeichert mit Entry/Exit/P&L/Datum, Trade History Tabelle auf Portfolio-Seite (letzte 20 Trades)
- **Trading Stats**: Win Rate, Total Trades, Avg Win, Avg Loss, Drawdown — automatisch berechnet aus geschlossenen Trades
- **Dashboard Enhancement**: Portfolio Summary Widget (Total Value, P&L, Open Positions, Drawdown, Win Rate), Top 3 Signals Widget mit Confidence Bars
- **Portfolio State Migration**: `closedTrades[]` und `peakValue` zum PortfolioState hinzugefügt, Backward-kompatibel mit altem localStorage
- Sidebar: 7 Nav-Items (+ Risk Guardian mit ShieldAlert Icon)
- Build: 0 Errors, 7 Routes | Backend: 8897 Tests grün

---

## ✅ ABGESCHLOSSEN: Multi-Asset Chart + WebSocket Live Stream (P2)

### Erstellt:
- **Multi-Asset Chart**: Generischer `AssetChart`-Komponent ersetzt BTC-only Chart. Tabs auf Dashboard für BTC, ETH, SOL, SPY, GLD — jeder mit eigenem synthetischen Datensatz + JARVIS Signal Overlay + Live-Preis
- **WebSocket Hook**: `use-websocket.ts` verbindet sich mit `/api/v1/stream/{symbol}`, Auto-Reconnect mit Exponential Backoff, Connection Status Tracking
- **WS Status Indicator**: Zap-Icon im Dashboard zeigt WebSocket-Verbindungsstatus (Live/Connecting/Offline)
- **API WS_BASE Export**: `api.ts` exportiert `WS_BASE` URL für WebSocket-Verbindungen
- **Live Preis Integration**: Chart zeigt Binance-Live-Preis wenn verfügbar, synthetischer Fallback
- 8 Custom Hooks (+ use-websocket)
- Build: 0 Errors, 9 Routes | Backend: 8897 Tests grün

---

## ✅ ABGESCHLOSSEN: AI Chat + Strategy Lab Backtest Engine

### Erstellt:
- **AI Chat Seite** (`/chat`): Vollständige Chat-UI mit JARVIS AI Assistant
  - Next.js API Route (`/api/chat`) — Server-seitig, API-Key bleibt auf dem Server
  - Claude API Integration (claude-sonnet-4-20250514) mit Trading-System-Prompt
  - Offline-Fallback mit kontextbezogenen Antworten (Regime, Signals, Risk, Strategy)
  - Portfolio-Kontext wird automatisch an Claude gesendet (Regime, P&L, Positions, Drawdown)
  - Quick-Prompt Buttons, Markdown-Rendering, Chat-Verlauf, Clear-Button
  - Konfiguration: `ANTHROPIC_API_KEY` in `.env.local` (optional — funktioniert auch ohne)
- **Strategy Lab Backtest Engine** (`/strategy-lab`): Voll funktionaler Backtest
  - Deterministische Backtest-Simulation über 90 Tage, 5 Assets (BTC, ETH, SOL, SPY, GLD)
  - 3 Strategien wählbar (Momentum, Mean Reversion, Combined) mit Visual Feedback
  - Performance Stats: Total Return, Win Rate, Sharpe Ratio, Max Drawdown, Avg Win/Loss, Profit Factor
  - SVG Equity Curve Chart mit Fill und Grid
  - Trade Log Tabelle (letzte 20 Trades mit Entry/Exit/P&L)
- Sidebar: 9 Nav-Items (+ AI Chat mit MessageSquare Icon)
- Build: 0 Errors, 9 Routes (8 Pages + 1 API) | Backend: 8897 Tests grün

---

## ✅ ABGESCHLOSSEN: Landing Page + Waitlist (Phase 0)

### Erstellt:
- **Landing Page** (`/landing`): Öffentliche Marketing-Seite ohne Sidebar
  - Hero Section mit Gradient-Background, Tagline "Trade Smarter with JARVIS", CTAs (Join Waitlist + Try Demo)
  - Social Proof Stats (8,890+ Tests, 100% FAS Compliance, 0.76ms P95, 96%+ Coverage)
  - 6 Feature Highlights mit Icons (AI Intelligence, Signals, Strategy Lab, Risk Guardian, Radar, Paper Trading)
  - USP Banner: Unique Timeframe Slider Feature
  - Pricing Section: 3 Tiers (Free €0 / Pro €29 / Enterprise €199) mit Feature-Vergleich
  - Waitlist Formular: Email-Eingabe → localStorage, Bestätigung mit Counter
  - Professioneller Footer mit Navigation + Social Icons
  - Fixed Navbar mit Glassmorphism-Effekt + "Open App" Button
- **AI Chat Error Handling**: Verbesserte Fehlermeldungen (Credit Error, Key Error statt stiller Offline-Fallback)
- Build: 0 Errors, 10 Routes (9 Pages + 1 API) | Backend: 8897 Tests grün

---

## ✅ ABGESCHLOSSEN: Timeframe Slider (USP) + Toast System + Mobile Sidebar

### Erstellt:
- **Timeframe Slider (USP)** (`timeframe-slider.tsx`): Das Alleinstellungsmerkmal von JARVIS-Trader
  - Slider von 1m bis 1W (7 Stufen: 1m, 5m, 15m, 1H, 4H, 1D, 1W)
  - Automatische Strategie-Empfehlung pro Timeframe (Scalping → Momentum → Combined → Mean Reversion)
  - Farbcodierte Strategy-Anzeige + Beschreibung + Bar-Type Info
  - Integriert im Dashboard zwischen Regime-Anzeige und Chart
  - Timeframe-Badge im Chart-Header zeigt aktive Auswahl
- **Toast Notification System** (`toast.tsx`): Lightweight Context-based Toast Provider
  - 4 Typen: success (grün), error (rot), warning (gelb), info (blau)
  - Auto-dismiss nach 3s, manuelles Dismiss per X-Button
  - Fixed bottom-right, slide-in Animation
  - Integriert in Signals-Seite (Accept/Close) und Portfolio-Seite (Close/Close All)
- **Mobile Sidebar Auto-Collapse**: Responsive Sidebar für mobile Geräte
  - Auto-Detect < 768px via matchMedia
  - Sidebar hidden auf Mobile, Hamburger-Button öffnet Overlay
  - Click-outside-to-close mit Backdrop-Overlay
  - Sidebar Props erweitert: `mobile`, `mobileOpen`
- Build: 0 Errors, 10 Routes (9 Pages + 1 API) | Backend: 8897 Tests grün

---

## ✅ ABGESCHLOSSEN: Supabase Auth (Phase 2) + Tailwind Fix

### Erstellt:
- **Supabase Auth Integration**: Vollständige Authentifizierung mit Email/Passwort + Google OAuth
  - `@supabase/supabase-js` + `@supabase/ssr` installiert
  - Supabase Browser-Client (`src/lib/supabase/client.ts`) + Server-Client (`src/lib/supabase/server.ts`)
  - **Login-Seite** (`/login`): Email/Passwort + Google SSO, Redirect nach Login, Error Handling
  - **Register-Seite** (`/register`): Email/Passwort + Bestätigungs-Email-Flow + Google SSO
  - **Auth Layout** (`(auth)/layout.tsx`): Zentriertes Layout ohne Sidebar
  - **OAuth Callback** (`/auth/callback/route.ts`): Server-seitige Code→Session Exchange
  - **Auth Hook** (`use-auth.ts`): Reaktiver User-State + Sign-Out Funktion
  - **Middleware** (`src/middleware.ts`): Route Protection — unauthentifizierte User → `/login`, authentifizierte User weg von `/login`+`/register`
  - Public Paths: `/landing`, `/login`, `/register`, `/auth`
  - API-Routes (`/api/*`) nicht von Auth-Middleware blockiert
- **Sidebar User Section**: User-Email + Sign-Out Button im Sidebar-Footer
- **Landing Page Update**: CTAs verlinken auf `/login` + `/register` statt interner Navigations
- **Tailwind CSS Fix**: `<alpha-value>` Platzhalter in allen Custom Colors (`tailwind.config.ts`) — behebt fehlende Styles bei Opacity-Modifiern (`bg-card/30`, `border-border/50`, etc.)
- **ENV**: `NEXT_PUBLIC_SUPABASE_URL` + `NEXT_PUBLIC_SUPABASE_ANON_KEY` in `.env.local` (Platzhalter — Supabase-Projekt erstellen und Keys eintragen)
- Build: 0 Errors, 13 Routes (11 Pages + 2 API) + Middleware | Backend: 8897 Tests grün

### Setup-Anleitung (Supabase):
1. Supabase-Projekt erstellen auf https://supabase.com
2. Project URL + Anon Key kopieren → `.env.local` eintragen
3. Google OAuth: Supabase Dashboard → Authentication → Providers → Google aktivieren
4. Redirect-URL in Google Cloud Console: `https://YOUR_PROJECT.supabase.co/auth/v1/callback`

---

## ✅ ABGESCHLOSSEN: Supabase DB-Persistenz + Tier System + Feature-Gating

### Erstellt:
- **Supabase DB Schema** (`supabase/schema.sql`): Vollständiges Datenbankschema mit RLS
  - `profiles` Tabelle: User-Profil mit `tier` (free/pro/enterprise), Display-Name
  - `portfolios` Tabelle: Portfolio-State (Capital, Positions als JSONB, Peak Value)
  - `trades` Tabelle: Geschlossene Trades mit allen Details (Entry/Exit/P&L)
  - `user_settings` Tabelle: App-Settings als JSONB
  - **Row Level Security**: Jeder User kann nur eigene Daten lesen/schreiben
  - **Auto-Trigger**: Profile + Portfolio + Settings werden automatisch bei Signup erstellt
  - **Index**: `trades_user_id_idx` für schnelle Trade-Abfragen
- **Portfolio-Persistenz** (`use-portfolio.ts`): Supabase-Sync mit localStorage-Cache
  - Lädt von Supabase beim Mount, fällt auf localStorage zurück
  - Open/Close Trade → sofortiger Supabase-Write
  - Preis-Updates → localStorage sofort, Supabase debounced (10s)
  - Closed Trades → in `trades` Tabelle geschrieben
  - Migration: Bestehende localStorage-Daten werden bei erstem Login zu Supabase migriert
- **Settings-Persistenz** (`use-settings.ts`): Supabase-Sync mit localStorage-Cache
  - Lädt Settings von Supabase, migriert localStorage-Daten bei erstem Login
  - Jede Setting-Änderung → Supabase + localStorage parallel
- **User Profile Hook** (`use-profile.ts`): Profil + Tier aus Supabase
  - `isPro`, `isEnterprise` Convenience-Flags
  - Fallback auf `free` Tier wenn kein Profil vorhanden
- **Feature-Gating** (`upgrade-gate.tsx`): Tier-basierte Feature-Sperre
  - Zeigt Upgrade-Prompt mit Link zur Pricing-Seite
  - **AI Chat**: Nur für Pro+ User zugänglich
  - **Strategy Lab + Backtesting**: Nur für Pro+ User zugänglich
- Build: 0 Errors, 13 Routes + Middleware | Backend: 8897 Tests grün

### Setup-Anleitung (Supabase DB):
1. Supabase Dashboard → SQL Editor
2. `supabase/schema.sql` Inhalt einfügen und ausführen
3. Fertig — Auth-Trigger erstellt automatisch Profile bei Signup

---

## ✅ ABGESCHLOSSEN: Free-Tier Limits + OOD Warnings + Trade Journal Export

### Erstellt:
- **Tier-Limit Konstanten** (`constants.ts`): `TIER_LIMITS` + `FREE_ASSETS` für zentrales Feature-Gating
  - Free: 3 Assets (BTC/ETH/SOL), $10k Capital, 15min Signal-Delay, kein OOD
  - Pro: Alle Assets, $500k Capital, Echtzeit, OOD-Warnungen
  - Enterprise: Unbegrenzt
- **Signals-Seite** — Tier-basiertes Filtering:
  - Free-Tier: Nur 3 Assets sichtbar + "15min delay" Badge + "3/8 assets" Badge
  - OOD-Spalte: Pro zeigt OK/OOD Status detailliert, Free zeigt Lock-Icon
  - Asset-Zähler zeigt Free-Usern wie viele Assets mit Upgrade verfügbar wären
- **Radar-Seite** — Free-Tier Asset-Filter: Nur 3 Assets im Opportunity Scanner
- **Settings-Seite** — Vollständige Tier-Integration:
  - Subscription-Info Card oben (Plan-Name, Limits, Upgrade-Button)
  - Capital-Input mit Max-Limit pro Tier ($10k Free / $500k Pro)
  - Asset-Toggle: Gesperrte Assets ausgegraut mit Lock-Icon + Hinweis
- **Trade Journal Export** (`portfolio/page.tsx`):
  - CSV-Export Button in Trade History (Download als `jarvis-trades-YYYY-MM-DD.csv`)
  - Alle Felder: Asset, Direction, Entry, Exit, Size, Capital, P&L, Return%, Dates
  - "Trade History" → "Trade Journal" umbenannt
- Build: 0 Errors, 13 Routes + Middleware | Backend: 8897 Tests grün

---

## ✅ ABGESCHLOSSEN: MVP Launch-Readiness (Legal + Error Handling + PWA + SEO)

### Erstellt:
- **Rechtliche Pflichtseiten** (DSGVO-konform):
  - `/legal/disclaimer` — Kein Anlageberater, Paper Trading = Simulation, Risikohinweis
  - `/legal/privacy` — DSGVO Datenschutzerklärung (Art. 6, 15-21), Supabase EU, Rechte
  - `/legal/terms` — AGB mit Tiers, Haftung, Kündigung, deutsches Recht
  - `/legal/imprint` — Impressum nach §5 TMG
  - Route Group `(legal)/` mit eigenem Layout (Nav + Legal-Links)
  - `/legal` als Public Path in Middleware (kein Login nötig)
  - Footer der Landing Page mit Links zu allen Legal-Seiten
- **Error Boundary** (`(app)/error.tsx`): Fängt Crashes in der App ab, zeigt "Try Again"-Button
- **Custom 404** (`not-found.tsx`): Branded 404-Seite mit Links zu Dashboard + Landing
- **Loading Skeleton** (`(app)/loading.tsx`): Animierte Platzhalter während Seitenlade
- **PWA Manifest** (`public/manifest.json`): Standalone-App, Theme-Color, App-Name
- **SEO + Meta** (`layout.tsx`):
  - Open Graph Tags (Title, Description, Site Name)
  - Twitter Card Tags
  - Apple Web App Meta (standalone capable)
  - Viewport mit Theme-Color
  - Dynamische Title-Templates (`%s | JARVIS Trader`)
- Build: 0 Errors, **17 Routes** (13 App + 4 Legal + 2 API) + Middleware | Backend: 8897 Tests grün

### 🏁 MVP STATUS: LAUNCH-READY

| Phase | Status |
|-------|--------|
| Phase 0: Landing Page + Waitlist | ✅ |
| Phase 1: JARVIS API Connection | ✅ |
| Phase 2: Auth (Supabase) | ✅ |
| Phase 3: Charts + Signals + Radar | ✅ |
| Phase 4: Paper Trading + Dashboard | ✅ |
| Tier System + Feature Gating | ✅ |
| DB Persistence (Supabase) | ✅ |
| Legal Pages (DSGVO) | ✅ |
| Error Handling + 404 | ✅ |
| PWA + SEO | ✅ |
| **Stripe Payments** | ⏭️ Übersprungen |
| **Deployment** | ⏭️ Übersprungen |

---

## ✅ ABGESCHLOSSEN: Admin/Owner Enterprise Override + PWA Icons

### Erstellt:
- **Admin Enterprise Override** (`use-profile.ts`): Owner-Email bekommt immer Enterprise-Tier
  - `ADMIN_EMAILS` Liste: `mfaix90@gmail.com` → automatisch Enterprise
  - Client-seitig im Profile-Hook — kein DB-Change nötig
  - Alle Feature-Gates deaktiviert für Admin (isPro=true, isEnterprise=true)
- **PWA Icons** (`scripts/generate-icons.mjs`): Programmatisch generierte App-Icons
  - Sharp-basierter Generator: "J" auf blauem Gradient-Hintergrund
  - `icon-192.png` + `icon-512.png` in `public/`
  - Abgerundete Ecken, system-ui Font, professionelles Design
- Build: 0 Errors | Backend: 8897 Tests grün

---

## ✅ ABGESCHLOSSEN: Binance WebSocket Live-Prices + Price Alert System

### Erstellt:
- **Binance WebSocket Live-Stream** (`use-prices.ts`): Echtzeit-Preise via WebSocket
  - Verbindet sich mit `wss://stream.binance.com:9443/stream` (Combined Stream)
  - Streams: `btcusdt@miniTicker`, `ethusdt@miniTicker`, `solusdt@miniTicker`
  - Auto-Reconnect mit Exponential Backoff (max 10 Versuche, max 30s Delay)
  - REST-Polling als Fallback wenn WebSocket fehlschlägt
  - Synthetische Preise für Nicht-Crypto-Assets unverändert
  - Neues Return-Feld: `wsConnected` zeigt WebSocket-Status
  - Dashboard + Signals zeigen "WS Live" / "REST Polling" / "Synthetic" Status
- **Price Alert System** (`use-alerts.ts` + `/alerts` Seite):
  - Alerts erstellen: Asset + Condition (above/below) + Zielpreis
  - Echtzeit-Prüfung gegen Live-Preise (WebSocket-Speed für Crypto)
  - **Browser Notifications**: Nativer Notification API Support mit Permission-Request
  - Triggered Alerts mit Zeitstempel, Clear-Funktion
  - localStorage-Persistenz für Alerts
  - Neue Seite `/alerts` mit Create-Form, Active Alerts (mit Distanz-Anzeige), Triggered History
- **Sidebar Update**: Neuer Nav-Item "Price Alerts" mit BellRing-Icon (9 → 10 Nav-Items)
- Build: 0 Errors, **18 Routes** (14 App + 4 Legal + 2 API) + Middleware

---

## ✅ ABGESCHLOSSEN: Signal-Alerts + Watchlist + Equity Curve

### Erstellt:
- **Signal-Alerts** (`use-signal-alerts.ts`): Automatische Browser-Benachrichtigungen bei High-Confidence Signals
  - Threshold: ≥70% Confidence → Browser Notification
  - Cooldown: 1 Minute pro Asset (kein Spam)
  - Integriert in Signals-Seite — läuft automatisch im Hintergrund
- **Watchlist** (`components/dashboard/watchlist.tsx`): Anpassbare Asset-Favoriten auf dem Dashboard
  - Default: BTC, ETH, SOL — erweiterbar über Edit-Modus
  - Live-Preise mit Trend-Indikator (grün/rot Pfeile + %-Change)
  - Signal-Badges zeigen aktuelle JARVIS-Signale pro Asset
  - localStorage-Persistenz
  - Integriert im Dashboard neben den Stats
- **Equity Curve** (`components/chart/equity-curve.tsx`): SVG Portfolio-Performance-Chart
  - Zeigt Equity-Verlauf basierend auf geschlossenen Trades
  - Grün bei Gewinn, Rot bei Verlust, mit Datenpunkten pro Trade
  - Y-Achse mit Grid, Start/End Labels
  - Integriert auf Portfolio-Seite (ab 2+ geschlossenen Trades sichtbar)
- Build: 0 Errors, **18 Routes** + Middleware

---

## ✅ ABGESCHLOSSEN: Real Binance Charts + Leaderboard + Achievements

### Erstellt:
- **Echte Binance OHLC-Charts** (`use-binance-klines.ts` + `asset-chart.tsx`):
  - Crypto-Charts (BTC, ETH, SOL) zeigen echte Binance Klines statt synthetischer Daten
  - REST-Fetch von `api.binance.com/api/v3/klines` mit konfigurierbarem Interval
  - Unterstützt: 1m, 5m, 15m, 1h, 4h, 1d, 1w Timeframes
  - Echtes Volumen in Histogram-Overlay
  - "LIVE DATA" Badge bei Crypto, "Synthetic Data" bei Nicht-Crypto
  - Fallback auf synthetische Daten wenn Binance nicht erreichbar
- **Community Leaderboard** (`/leaderboard`):
  - Top-3 Podium mit Gold/Silber/Bronze
  - Vollständige Ranking-Tabelle mit Return, Win Rate, Trades, Max Drawdown
  - 3 Sortier-Tabs: Return, Win Rate, Risk-Adjusted (Return/Drawdown)
  - Current User wird automatisch eingeordnet (basierend auf echten Portfolio-Daten)
  - Tier-Badges (Free/Pro/Enterprise) pro Trader
  - Simulated Leaderboard-Daten (Supabase-Integration in v2)
- **Achievements/Gamification** (`use-achievements.ts`):
  - 13 Achievements in 3 Tier-Stufen (Bronze/Silver/Gold)
  - Kategorien: Trading Volume, Profitability, Win Rate, Streaks, Risk Management
  - Progress-Bars zeigen Fortschritt zu jedem Achievement
  - Integriert auf Portfolio-Seite mit Grid-Ansicht
  - Beispiele: "First Blood", "Hot Streak", "Master Trader", "Risk Manager"
- **Sidebar**: Neuer Nav-Item "Leaderboard" mit Trophy-Icon (11 Nav-Items)
- **Tailwind CSS Permanent Fix**: PostCSS + Tailwind Configs zu CommonJS konvertiert + predev Cache-Clean
- Build: 0 Errors, **23 Routes** + Middleware

---

## 🔜 NÄCHSTER SCHRITT

### Sofort (ohne Code):
1. Domain: **jarvis-trader.app** registrieren (~€15)
2. **Railway** Account: railway.app (kostenlos)
3. **Anthropic API Credits** aufladen für AI Chat

### Nächste Code-Features (Post-MVP):
1. Deployment auf Railway (Frontend + Backend)
2. Stripe Integration (Subscriptions, Checkout)
3. Capacitor.js (PWA → App Store)
4. Social Trading: Top-Trader folgen + kopieren
5. Leaderboard mit Supabase (echte User-Daten)
6. Notification Center (zentrale Benachrichtigungen)

---

*CLAUDE.md — Version 8.6.0 | März 2026*
*Backend 100% FAS-konform und abgeschlossen. FAS-Datei wird nicht mehr aktualisiert.*
