// =============================================================================
// src/lib/copilot-engine.ts — JARVIS Co-Pilot Intelligence (offline-first)
//
// Pure functions: no React, no side effects. Generates contextual responses
// based on market data, portfolio state, and user preferences.
// =============================================================================

import type { RegimeState } from "@/lib/types";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type RiskProfile = "conservative" | "moderate" | "aggressive";
export type Locale = "de" | "en";

export interface CoPilotContext {
  regime: RegimeState;
  ece: number;
  oodScore: number;
  metaUncertainty: number;
  strategy: string;
  selectedAsset: string;
  interval: string;
  slPercent: number;
  tpPercent: number;
  currentPrice: number;
  totalValue: number;
  drawdown: number;
  positionCount: number;
  closedTradeCount: number;
  realizedPnl: number;
  winRate: number;
  signalCount: number;
  topSignalAsset: string | null;
  topSignalDirection: string | null;
  topSignalConfidence: number;
  patterns: PatternInfo[];
}

export interface PatternInfo {
  type: string;
  description: string;
  confidence: number;
}

export interface ParsedAlert {
  asset: string;
  condition: "above" | "below";
  targetPrice: number;
}

export interface RiskRewardResult {
  ratio: number;
  riskAmount: number;
  rewardAmount: number;
  rating: "good" | "neutral" | "bad";
}

// ---------------------------------------------------------------------------
// Risk/Reward Calculator (Feature 2)
// ---------------------------------------------------------------------------

export function calculateRiskReward(
  entryPrice: number,
  slPercent: number,
  tpPercent: number,
): RiskRewardResult {
  const riskAmount = entryPrice * (slPercent / 100);
  const rewardAmount = entryPrice * (tpPercent / 100);
  const ratio = riskAmount > 0 ? rewardAmount / riskAmount : 0;
  const rating = ratio >= 2 ? "good" : ratio >= 1 ? "neutral" : "bad";
  return { ratio, riskAmount, rewardAmount, rating };
}

// ---------------------------------------------------------------------------
// Confidence Score (Feature 3)
// ---------------------------------------------------------------------------

const REGIME_MULTIPLIER: Record<string, number> = {
  RISK_ON: 1.0,
  RISK_OFF: 0.7,
  TRANSITION: 0.5,
  CRISIS: 0.3,
  UNKNOWN: 0.6,
};

export function calculateConfidence(
  ece: number,
  oodScore: number,
  signalConfidence: number,
  regime: RegimeState,
): number {
  const eceFactor = Math.max(0, 1 - ece * 5); // ECE 0.05 = 0.75, ECE 0 = 1.0
  const oodFactor = Math.max(0, 1 - oodScore);
  const regimeMul = REGIME_MULTIPLIER[regime] ?? 0.6;
  return Math.min(1, eceFactor * oodFactor * signalConfidence * regimeMul);
}

// ---------------------------------------------------------------------------
// Alert Parser (Feature 7)
// ---------------------------------------------------------------------------

const KNOWN_ASSETS = ["BTC", "ETH", "SOL", "SPY", "AAPL", "NVDA", "TSLA", "GLD", "OIL"];

export function parseAlertFromMessage(text: string): ParsedAlert | null {
  const upper = text.toUpperCase();

  // Find asset
  const asset = KNOWN_ASSETS.find((a) => upper.includes(a));
  if (!asset) return null;

  // Find price: $75,000 or $75000 or 75000 or 75.000
  const priceMatch = text.match(/\$?([\d.,]+)/);
  if (!priceMatch) return null;
  const price = parseFloat(priceMatch[1].replace(/[,\.]/g, (m, offset, str) => {
    // Handle European notation (75.000) vs decimal (75.50)
    const afterDot = str.slice(offset + 1);
    if (m === "." && afterDot.length === 3 && !afterDot.includes(".")) return "";
    if (m === ",") return "";
    return m;
  }));
  if (isNaN(price) || price <= 0) return null;

  // Determine condition
  const hasBelow = /below|unter|fällt|faellt|drops|falls|under/i.test(text);
  const condition: "above" | "below" = hasBelow ? "below" : "above";

  return { asset, condition, targetPrice: price };
}

// ---------------------------------------------------------------------------
// Strategy Labels
// ---------------------------------------------------------------------------

const STRATEGY_LABELS: Record<string, Record<Locale, string>> = {
  momentum: { de: "Momentum", en: "Momentum" },
  mean_reversion: { de: "Mean Reversion", en: "Mean Reversion" },
  combined: { de: "Combined", en: "Combined" },
  breakout: { de: "Breakout", en: "Breakout" },
  trend_following: { de: "Trend Following", en: "Trend Following" },
  scalping: { de: "Scalping", en: "Scalping" },
  swing_trading: { de: "Swing Trading", en: "Swing Trading" },
  custom: { de: "Custom", en: "Custom" },
};

function stratLabel(strategy: string, locale: Locale): string {
  return STRATEGY_LABELS[strategy]?.[locale] ?? strategy;
}

// ---------------------------------------------------------------------------
// Offline Response Generator (Feature 10)
// ---------------------------------------------------------------------------

export function generateOfflineResponse(
  userMessage: string,
  ctx: CoPilotContext,
  locale: Locale,
  riskProfile: RiskProfile,
): string {
  const msg = userMessage.toLowerCase();
  const de = locale === "de";
  const strat = stratLabel(ctx.strategy, locale);

  // --- Alert parsing (Feature 7) ---
  const alertParsed = parseAlertFromMessage(userMessage);
  if (alertParsed) {
    return de
      ? `✅ **Alert gesetzt** fuer ${alertParsed.asset} ${alertParsed.condition === "above" ? "ueber" : "unter"} $${alertParsed.targetPrice.toLocaleString()}\n\nDu wirst benachrichtigt sobald der Preis erreicht wird.`
      : `✅ **Alert set** for ${alertParsed.asset} ${alertParsed.condition} $${alertParsed.targetPrice.toLocaleString()}\n\nYou'll be notified when the price is reached.`;
  }

  // --- Chart Analysis ---
  if (msg.includes("analys") || msg.includes("chart") || msg.includes("muster") || msg.includes("pattern")) {
    return generateChartAnalysis(ctx, locale, riskProfile);
  }

  // --- Best Strategy ---
  if (msg.includes("beste strategie") || msg.includes("best strategy") || msg.includes("empfehl") || msg.includes("recommend")) {
    return generateStrategyRecommendation(ctx, locale, riskProfile);
  }

  // --- Risk/Reward ---
  if (msg.includes("r:r") || msg.includes("risk") || msg.includes("reward") || msg.includes("risiko")) {
    const rr = calculateRiskReward(ctx.currentPrice, ctx.slPercent, ctx.tpPercent);
    return generateRRResponse(rr, ctx, locale);
  }

  // --- Confidence ---
  if (msg.includes("konfidenz") || msg.includes("confidence") || msg.includes("sicher")) {
    const conf = calculateConfidence(ctx.ece, ctx.oodScore, ctx.topSignalConfidence, ctx.regime);
    return generateConfidenceResponse(conf, ctx, locale);
  }

  // --- Regime ---
  if (msg.includes("regime") || msg.includes("markt") || msg.includes("market")) {
    return generateRegimeResponse(ctx, locale);
  }

  // --- Portfolio ---
  if (msg.includes("portfolio") || msg.includes("position") || msg.includes("depot")) {
    return generatePortfolioResponse(ctx, locale);
  }

  // --- Daily Review ---
  if (msg.includes("tagesrueckblick") || msg.includes("tagesrückblick") || msg.includes("daily") || msg.includes("review") || msg.includes("zusammenfassung") || msg.includes("summary")) {
    return generateDailyReview(ctx, locale, riskProfile);
  }

  // --- Custom Strategy ---
  if (msg.includes("custom") || msg.includes("eigene")) {
    return de
      ? `## Eigene Strategie erstellen\n\n1. Waehle **Custom** im Strategy Panel\n2. Klicke auf **Rule Builder anzeigen**\n3. Fuege mindestens 1 BUY und 1 SELL Regel hinzu\n4. Beispiel: *IF RSI < 30 → BUY* + *IF RSI > 70 → SELL*\n5. Klicke **Run Backtest** um die Performance zu pruefen\n\n💡 *${riskProfile === "conservative" ? "Konservativ: Nutze engere RSI-Grenzen (35/65)" : riskProfile === "aggressive" ? "Aggressiv: Kombiniere MACD + EMA Crossover fuer mehr Signale" : "Moderat: RSI 30/70 ist ein guter Startpunkt"}*`
      : `## Create Custom Strategy\n\n1. Select **Custom** in the Strategy Panel\n2. Click **Show Rule Builder**\n3. Add at least 1 BUY and 1 SELL rule\n4. Example: *IF RSI < 30 → BUY* + *IF RSI > 70 → SELL*\n5. Click **Run Backtest** to check performance\n\n💡 *${riskProfile === "conservative" ? "Conservative: Use tighter RSI bounds (35/65)" : riskProfile === "aggressive" ? "Aggressive: Combine MACD + EMA crossover for more signals" : "Moderate: RSI 30/70 is a good starting point"}*`;
  }

  // --- Greeting ---
  if (msg.includes("hallo") || msg.includes("hello") || msg.includes("hi") || msg.includes("hey")) {
    return de
      ? `👋 Hallo! Ich bin **JARVIS**, dein AI Trading Co-Pilot.\n\nAktueller Markt: **${ctx.regime.replace("_", " ")}** | Asset: **${ctx.selectedAsset}** | Strategie: **${strat}**\n\nWie kann ich dir helfen? Nutze die Quick Actions oder frag mich etwas!`
      : `👋 Hello! I'm **JARVIS**, your AI Trading Co-Pilot.\n\nCurrent market: **${ctx.regime.replace("_", " ")}** | Asset: **${ctx.selectedAsset}** | Strategy: **${strat}**\n\nHow can I help? Use the Quick Actions or ask me anything!`;
  }

  // --- Help / Default ---
  return de
    ? `Ich kann dir bei folgenden Themen helfen:\n\n- **📊 Chart analysieren** — Muster & Levels erkennen\n- **🎯 Beste Strategie** — Empfehlung basierend auf Marktlage\n- **📈 R:R berechnen** — Risk/Reward fuer aktuellen Trade\n- **🔔 Alert setzen** — z.B. "Sag mir wenn BTC $75.000 erreicht"\n- **📋 Tagesrueckblick** — Zusammenfassung der heutigen Performance\n- **⚙️ Custom Strategie** — Eigene Regeln erstellen\n\nAktuell: **${ctx.regime.replace("_", " ")}** | ${ctx.selectedAsset} bei $${ctx.currentPrice.toLocaleString("en-US", { maximumFractionDigits: 2 })}`
    : `I can help you with:\n\n- **📊 Analyze Chart** — Detect patterns & levels\n- **🎯 Best Strategy** — Recommendation based on market conditions\n- **📈 Calculate R:R** — Risk/Reward for current trade\n- **🔔 Set Alert** — e.g. "Tell me when BTC hits $75,000"\n- **📋 Daily Review** — Today's performance summary\n- **⚙️ Custom Strategy** — Build your own rules\n\nCurrent: **${ctx.regime.replace("_", " ")}** | ${ctx.selectedAsset} at $${ctx.currentPrice.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
}

// ---------------------------------------------------------------------------
// Response Generators
// ---------------------------------------------------------------------------

function generateChartAnalysis(ctx: CoPilotContext, locale: Locale, riskProfile: RiskProfile): string {
  const de = locale === "de";
  const strat = stratLabel(ctx.strategy, locale);
  const rr = calculateRiskReward(ctx.currentPrice, ctx.slPercent, ctx.tpPercent);
  const conf = calculateConfidence(ctx.ece, ctx.oodScore, ctx.topSignalConfidence, ctx.regime);

  let patternText = "";
  if (ctx.patterns.length > 0) {
    const top = ctx.patterns[0];
    patternText = de
      ? `\n\n### Erkanntes Muster\n**${top.type}** (${(top.confidence * 100).toFixed(0)}% Konfidenz)\n${top.description}`
      : `\n\n### Detected Pattern\n**${top.type}** (${(top.confidence * 100).toFixed(0)}% confidence)\n${top.description}`;
  } else {
    patternText = de
      ? `\n\n*Kein starkes Chartmuster erkannt — Markt bewegt sich seitwaerts.*`
      : `\n\n*No strong chart pattern detected — market is ranging.*`;
  }

  const riskAdvice = riskProfile === "conservative"
    ? (de ? "Konservativ: Warte auf Bestaetigung bevor du einsteigst." : "Conservative: Wait for confirmation before entering.")
    : riskProfile === "aggressive"
    ? (de ? "Aggressiv: Fruehe Entries moeglich, aber enge Stops setzen." : "Aggressive: Early entries possible, but set tight stops.")
    : (de ? "Moderat: Standardmaessig mit dem Trend handeln." : "Moderate: Trade with the trend by default.");

  return de
    ? `## Chart-Analyse: ${ctx.selectedAsset}\n\n**Preis:** $${ctx.currentPrice.toLocaleString("en-US", { maximumFractionDigits: 2 })} | **Timeframe:** ${ctx.interval} | **Strategie:** ${strat}\n**Regime:** ${ctx.regime.replace("_", " ")} | **JARVIS Konfidenz:** ${(conf * 100).toFixed(0)}%\n**R:R:** 1:${rr.ratio.toFixed(1)} ${rr.rating === "good" ? "✅" : rr.rating === "neutral" ? "⚠️" : "❌"}${patternText}\n\n💡 *${riskAdvice}*`
    : `## Chart Analysis: ${ctx.selectedAsset}\n\n**Price:** $${ctx.currentPrice.toLocaleString("en-US", { maximumFractionDigits: 2 })} | **Timeframe:** ${ctx.interval} | **Strategy:** ${strat}\n**Regime:** ${ctx.regime.replace("_", " ")} | **JARVIS Confidence:** ${(conf * 100).toFixed(0)}%\n**R:R:** 1:${rr.ratio.toFixed(1)} ${rr.rating === "good" ? "✅" : rr.rating === "neutral" ? "⚠️" : "❌"}${patternText}\n\n💡 *${riskAdvice}*`;
}

function generateStrategyRecommendation(ctx: CoPilotContext, locale: Locale, riskProfile: RiskProfile): string {
  const de = locale === "de";

  let recommended: string;
  let reason: string;

  if (ctx.regime === "RISK_ON") {
    if (riskProfile === "aggressive") {
      recommended = "breakout";
      reason = de ? "Starker Trend + aggressive Risikobereitschaft = Breakout-Signale nutzen" : "Strong trend + aggressive risk = use breakout signals";
    } else {
      recommended = "trend_following";
      reason = de ? "Risk-On Markt ideal fuer Trend Following — mit dem Momentum gehen" : "Risk-On market ideal for Trend Following — ride the momentum";
    }
  } else if (ctx.regime === "RISK_OFF") {
    recommended = "mean_reversion";
    reason = de ? "Risk-Off Markt — Mean Reversion faengt Ueberreaktionen ab" : "Risk-Off market — Mean Reversion catches overreactions";
  } else if (ctx.regime === "CRISIS") {
    recommended = riskProfile === "conservative" ? "mean_reversion" : "combined";
    reason = de ? "Krisenmodus — defensiv handeln, nur hochkonfidente Setups" : "Crisis mode — trade defensively, only high-confidence setups";
  } else {
    recommended = "combined";
    reason = de ? "Markt im Uebergang — Combined Strategie deckt mehrere Szenarien ab" : "Market in transition — Combined strategy covers multiple scenarios";
  }

  const recLabel = stratLabel(recommended, locale);
  const currentLabel = stratLabel(ctx.strategy, locale);

  const isSame = ctx.strategy === recommended;

  return de
    ? `## Strategieempfehlung\n\n**Empfohlen:** ${recLabel} ${isSame ? "✅ (bereits aktiv)" : ""}\n**Grund:** ${reason}\n\n${!isSame ? `Aktuelle Strategie (${currentLabel}) ${ctx.regime === "CRISIS" ? "ist riskant" : "funktioniert"} im ${ctx.regime.replace("_", " ")} Markt${ctx.regime === "CRISIS" ? " — Wechsel empfohlen." : ", aber ${recLabel} waere optimaler."}` : "Deine aktuelle Strategie passt gut zur Marktlage!"}\n\n${riskProfile === "conservative" ? "🛡️ *Konservativ: SL auf ${ctx.slPercent}% halten, nur starke Signale handeln.*" : riskProfile === "aggressive" ? "🔥 *Aggressiv: TP auf ${ctx.tpPercent}% erhoehen, mehr Signale nutzen.*" : "⚖️ *Moderat: Standard-Parameter beibehalten.*"}`
    : `## Strategy Recommendation\n\n**Recommended:** ${recLabel} ${isSame ? "✅ (already active)" : ""}\n**Reason:** ${reason}\n\n${!isSame ? `Current strategy (${currentLabel}) ${ctx.regime === "CRISIS" ? "is risky" : "works"} in ${ctx.regime.replace("_", " ")} market${ctx.regime === "CRISIS" ? " — consider switching." : ", but ${recLabel} would be more optimal."}` : "Your current strategy fits the market well!"}\n\n${riskProfile === "conservative" ? "🛡️ *Conservative: Keep SL at ${ctx.slPercent}%, only trade strong signals.*" : riskProfile === "aggressive" ? "🔥 *Aggressive: Increase TP to ${ctx.tpPercent}%, use more signals.*" : "⚖️ *Moderate: Keep default parameters.*"}`;
}

function generateRRResponse(rr: RiskRewardResult, ctx: CoPilotContext, locale: Locale): string {
  const de = locale === "de";
  const icon = rr.rating === "good" ? "✅" : rr.rating === "neutral" ? "⚠️" : "❌";

  return de
    ? `## Risk/Reward Berechnung ${icon}\n\n**Entry:** $${ctx.currentPrice.toLocaleString("en-US", { maximumFractionDigits: 2 })}\n**Stop Loss:** ${ctx.slPercent}% → $${rr.riskAmount.toFixed(2)} Risiko\n**Take Profit:** ${ctx.tpPercent}% → $${rr.rewardAmount.toFixed(2)} Gewinn\n\n**R:R = 1:${rr.ratio.toFixed(1)}** — Fuer jeden $1 Risiko = $${rr.ratio.toFixed(1)} potentieller Gewinn\n\n${rr.rating === "good" ? "Gutes Setup! R:R ueber 1:2 ist professionell." : rr.rating === "neutral" ? "Akzeptabel, aber R:R unter 1:2 — TP erhoehen oder SL enger setzen." : "Schlechtes R:R! Nicht handeln ohne Anpassung der Parameter."}`
    : `## Risk/Reward Calculation ${icon}\n\n**Entry:** $${ctx.currentPrice.toLocaleString("en-US", { maximumFractionDigits: 2 })}\n**Stop Loss:** ${ctx.slPercent}% → $${rr.riskAmount.toFixed(2)} at risk\n**Take Profit:** ${ctx.tpPercent}% → $${rr.rewardAmount.toFixed(2)} potential gain\n\n**R:R = 1:${rr.ratio.toFixed(1)}** — For every $1 risk = $${rr.ratio.toFixed(1)} potential reward\n\n${rr.rating === "good" ? "Great setup! R:R above 1:2 is professional grade." : rr.rating === "neutral" ? "Acceptable, but R:R below 1:2 — increase TP or tighten SL." : "Poor R:R! Don't trade without adjusting parameters."}`;
}

function generateConfidenceResponse(conf: number, ctx: CoPilotContext, locale: Locale): string {
  const de = locale === "de";
  const pct = (conf * 100).toFixed(0);
  const icon = conf > 0.6 ? "✅" : conf > 0.3 ? "⚠️" : "❌";

  const factors = [];
  if (de) {
    factors.push(`ECE Kalibrierung: ${ctx.ece < 0.05 ? "gut" : "eingeschraenkt"} (${(ctx.ece * 100).toFixed(1)}%)`);
    factors.push(`OOD Score: ${ctx.oodScore < 0.3 ? "normal" : ctx.oodScore < 0.6 ? "erhoet" : "hoch"} (${(ctx.oodScore * 100).toFixed(0)}%)`);
    factors.push(`Signal Konfidenz: ${(ctx.topSignalConfidence * 100).toFixed(0)}%`);
    factors.push(`Regime Faktor: ${ctx.regime.replace("_", " ")} (${((REGIME_MULTIPLIER[ctx.regime] ?? 0.6) * 100).toFixed(0)}%)`);
  } else {
    factors.push(`ECE Calibration: ${ctx.ece < 0.05 ? "good" : "limited"} (${(ctx.ece * 100).toFixed(1)}%)`);
    factors.push(`OOD Score: ${ctx.oodScore < 0.3 ? "normal" : ctx.oodScore < 0.6 ? "elevated" : "high"} (${(ctx.oodScore * 100).toFixed(0)}%)`);
    factors.push(`Signal Confidence: ${(ctx.topSignalConfidence * 100).toFixed(0)}%`);
    factors.push(`Regime Factor: ${ctx.regime.replace("_", " ")} (${((REGIME_MULTIPLIER[ctx.regime] ?? 0.6) * 100).toFixed(0)}%)`);
  }

  return de
    ? `## JARVIS Konfidenz: ${pct}% ${icon}\n\n${factors.map((f) => `- ${f}`).join("\n")}\n\n**Formel:** (1-ECE) × (1-OOD) × Signal × Regime\n\n${conf > 0.6 ? "Hohe Konfidenz — Signale sind zuverlaessig." : conf > 0.3 ? "Mittlere Konfidenz — mit Vorsicht handeln." : "Niedrige Konfidenz — besser abwarten oder Positionsgroesse reduzieren."}`
    : `## JARVIS Confidence: ${pct}% ${icon}\n\n${factors.map((f) => `- ${f}`).join("\n")}\n\n**Formula:** (1-ECE) × (1-OOD) × Signal × Regime\n\n${conf > 0.6 ? "High confidence — signals are reliable." : conf > 0.3 ? "Medium confidence — trade with caution." : "Low confidence — better to wait or reduce position size."}`;
}

function generateRegimeResponse(ctx: CoPilotContext, locale: Locale): string {
  const de = locale === "de";
  const regimeInfo: Record<string, Record<Locale, string>> = {
    RISK_ON: {
      de: "**Risk On** — Maerkte sind optimistisch. Trend Following und Momentum Strategien funktionieren am besten. Breitere Stop-Losses moeglich.",
      en: "**Risk On** — Markets are optimistic. Trend Following and Momentum strategies work best. Wider stop-losses acceptable.",
    },
    RISK_OFF: {
      de: "**Risk Off** — Maerkte sind vorsichtig. Mean Reversion und defensive Strategien bevorzugen. Engere Stop-Losses empfohlen.",
      en: "**Risk Off** — Markets are cautious. Prefer Mean Reversion and defensive strategies. Tighter stop-losses recommended.",
    },
    CRISIS: {
      de: "**Krise** — Maerkte im Stressmodus. Positionen reduzieren, nur hochkonfidente Setups handeln. Gold (GLD) als Safe Haven.",
      en: "**Crisis** — Markets under stress. Reduce positions, only trade high-confidence setups. Gold (GLD) as safe haven.",
    },
    TRANSITION: {
      de: "**Uebergang** — Regime wechselt. Signale sind weniger zuverlaessig. Abwarten oder Combined Strategie nutzen.",
      en: "**Transition** — Regime is changing. Signals are less reliable. Wait or use Combined strategy.",
    },
    UNKNOWN: {
      de: "**Unbekannt** — Nicht genug Daten fuer Regime-Erkennung. Vorsichtig handeln.",
      en: "**Unknown** — Not enough data for regime detection. Trade cautiously.",
    },
  };

  const info = regimeInfo[ctx.regime]?.[locale] ?? regimeInfo.UNKNOWN[locale];

  return de
    ? `## Markt-Regime\n\n${info}\n\n- ECE: ${(ctx.ece * 100).toFixed(1)}% ${ctx.ece < 0.05 ? "✅" : "⚠️"}\n- OOD: ${(ctx.oodScore * 100).toFixed(0)}% ${ctx.oodScore < 0.3 ? "✅" : "⚠️"}\n- Meta-Unsicherheit: ${(ctx.metaUncertainty * 100).toFixed(0)}%`
    : `## Market Regime\n\n${info}\n\n- ECE: ${(ctx.ece * 100).toFixed(1)}% ${ctx.ece < 0.05 ? "✅" : "⚠️"}\n- OOD: ${(ctx.oodScore * 100).toFixed(0)}% ${ctx.oodScore < 0.3 ? "✅" : "⚠️"}\n- Meta-Uncertainty: ${(ctx.metaUncertainty * 100).toFixed(0)}%`;
}

function generatePortfolioResponse(ctx: CoPilotContext, locale: Locale): string {
  const de = locale === "de";
  const pnlIcon = ctx.realizedPnl >= 0 ? "📈" : "📉";

  return de
    ? `## Portfolio Uebersicht ${pnlIcon}\n\n- **Gesamtwert:** $${ctx.totalValue.toLocaleString("en-US", { maximumFractionDigits: 0 })}\n- **Offene Positionen:** ${ctx.positionCount}\n- **Realisierter P&L:** ${ctx.realizedPnl >= 0 ? "+" : ""}$${ctx.realizedPnl.toFixed(0)}\n- **Drawdown:** ${ctx.drawdown.toFixed(2)}%${ctx.drawdown > 10 ? " ⚠️" : ""}\n- **Win Rate:** ${ctx.winRate.toFixed(0)}% (${ctx.closedTradeCount} Trades)\n\n${ctx.drawdown > 10 ? "⚠️ *Drawdown ueber 10% — Positionsgroessen reduzieren!*" : ctx.drawdown > 5 ? "💡 *Drawdown erhoet — vorsichtiger handeln.*" : "✅ *Portfolio sieht gesund aus.*"}`
    : `## Portfolio Overview ${pnlIcon}\n\n- **Total Value:** $${ctx.totalValue.toLocaleString("en-US", { maximumFractionDigits: 0 })}\n- **Open Positions:** ${ctx.positionCount}\n- **Realized P&L:** ${ctx.realizedPnl >= 0 ? "+" : ""}$${ctx.realizedPnl.toFixed(0)}\n- **Drawdown:** ${ctx.drawdown.toFixed(2)}%${ctx.drawdown > 10 ? " ⚠️" : ""}\n- **Win Rate:** ${ctx.winRate.toFixed(0)}% (${ctx.closedTradeCount} trades)\n\n${ctx.drawdown > 10 ? "⚠️ *Drawdown above 10% — reduce position sizes!*" : ctx.drawdown > 5 ? "💡 *Drawdown elevated — trade more cautiously.*" : "✅ *Portfolio looks healthy.*"}`;
}

// ---------------------------------------------------------------------------
// Daily Review (Feature 9)
// ---------------------------------------------------------------------------

export function generateDailyReview(ctx: CoPilotContext, locale: Locale, riskProfile: RiskProfile): string {
  const de = locale === "de";
  const conf = calculateConfidence(ctx.ece, ctx.oodScore, ctx.topSignalConfidence, ctx.regime);
  const rr = calculateRiskReward(ctx.currentPrice, ctx.slPercent, ctx.tpPercent);

  const outlook = ctx.regime === "RISK_ON"
    ? (de ? "Positiv — Trend-Strategien bevorzugen" : "Positive — favor trend strategies")
    : ctx.regime === "RISK_OFF"
    ? (de ? "Vorsichtig — defensive Setups suchen" : "Cautious — look for defensive setups")
    : ctx.regime === "CRISIS"
    ? (de ? "Defensiv — nur hochkonfidente Trades" : "Defensive — only high-confidence trades")
    : (de ? "Abwarten — Regime-Bestaetigung noetig" : "Wait — regime confirmation needed");

  return de
    ? `## Tagesrueckblick 📋\n\n### Markt\n- **Regime:** ${ctx.regime.replace("_", " ")}\n- **JARVIS Konfidenz:** ${(conf * 100).toFixed(0)}%\n- **Aktive Signale:** ${ctx.signalCount}\n\n### Portfolio\n- **Wert:** $${ctx.totalValue.toLocaleString("en-US", { maximumFractionDigits: 0 })}\n- **P&L:** ${ctx.realizedPnl >= 0 ? "+" : ""}$${ctx.realizedPnl.toFixed(0)}\n- **Win Rate:** ${ctx.winRate.toFixed(0)}%\n- **Drawdown:** ${ctx.drawdown.toFixed(2)}%\n\n### Ausblick\n${outlook}\n- R:R aktuell: 1:${rr.ratio.toFixed(1)} ${rr.rating === "good" ? "✅" : "⚠️"}\n\n💡 *${riskProfile === "conservative" ? "Konservativ: Morgen nur Top-Signale handeln." : riskProfile === "aggressive" ? "Aggressiv: Wenn Regime Risk-On bleibt, Exposure erhoehen." : "Moderat: Wie gewohnt weiter handeln."}*`
    : `## Daily Review 📋\n\n### Market\n- **Regime:** ${ctx.regime.replace("_", " ")}\n- **JARVIS Confidence:** ${(conf * 100).toFixed(0)}%\n- **Active Signals:** ${ctx.signalCount}\n\n### Portfolio\n- **Value:** $${ctx.totalValue.toLocaleString("en-US", { maximumFractionDigits: 0 })}\n- **P&L:** ${ctx.realizedPnl >= 0 ? "+" : ""}$${ctx.realizedPnl.toFixed(0)}\n- **Win Rate:** ${ctx.winRate.toFixed(0)}%\n- **Drawdown:** ${ctx.drawdown.toFixed(2)}%\n\n### Outlook\n${outlook}\n- Current R:R: 1:${rr.ratio.toFixed(1)} ${rr.rating === "good" ? "✅" : "⚠️"}\n\n💡 *${riskProfile === "conservative" ? "Conservative: Only trade top signals tomorrow." : riskProfile === "aggressive" ? "Aggressive: If regime stays Risk-On, increase exposure." : "Moderate: Continue trading as usual."}*`;
}

// ---------------------------------------------------------------------------
// Trade Review (KI-Coaching)
// ---------------------------------------------------------------------------

export function generateTradeReview(
  trade: {
    asset: string;
    direction: "LONG" | "SHORT";
    entryPrice: number;
    exitPrice: number;
    pnl: number;
    pnlPercent: number;
    holdingPeriod?: string;
  },
  ctx: CoPilotContext,
  locale: Locale,
  riskProfile: RiskProfile
): string {
  const won = trade.pnl > 0;
  const rrActual = trade.exitPrice && trade.entryPrice
    ? Math.abs(trade.exitPrice - trade.entryPrice) / (trade.entryPrice * (ctx.slPercent / 100))
    : 0;

  if (locale === "de") {
    return [
      `## Trade Review: ${trade.asset} ${trade.direction}`,
      "",
      `**Ergebnis:** ${won ? "✅ Gewinn" : "❌ Verlust"} (${trade.pnl >= 0 ? "+" : ""}${trade.pnl.toFixed(2)} / ${trade.pnlPercent?.toFixed(1) ?? "—"}%)`,
      "",
      `**Analyse:**`,
      won
        ? `- Guter Einstieg bei $${trade.entryPrice.toLocaleString()}. ${rrActual > 1.5 ? "Exzellentes R:R Verhältnis." : "R:R akzeptabel."}`
        : `- Entry bei $${trade.entryPrice.toLocaleString()} war ${rrActual < 0.5 ? "zu früh — Signal war noch nicht bestätigt" : "im Rahmen, aber Markt lief dagegen"}.`,
      `- Regime war ${ctx.regime}${ctx.regime === "CRISIS" ? " — schwieriges Umfeld für Trades" : ""}.`,
      `- ${riskProfile === "conservative" ? "Konservative Positionsgröße war korrekt." : riskProfile === "aggressive" ? "Aggressive Positionierung erhöht Risiko." : "Moderate Positionierung war angemessen."}`,
      "",
      `**Empfehlung:**`,
      won
        ? `- Weiter so! ${rrActual > 2 ? "Take-Profit-Level war gut gewählt." : "Erwäge größere TP-Ziele für besseres R:R."}`
        : `- ${ctx.oodScore > 0.5 ? "OOD-Score war hoch — in solchen Situationen besser warten." : "Prüfe die Signal-Konfidenz vor dem nächsten Trade."}`,
    ].join("\n");
  }

  return [
    `## Trade Review: ${trade.asset} ${trade.direction}`,
    "",
    `**Result:** ${won ? "✅ Win" : "❌ Loss"} (${trade.pnl >= 0 ? "+" : ""}${trade.pnl.toFixed(2)} / ${trade.pnlPercent?.toFixed(1) ?? "—"}%)`,
    "",
    `**Analysis:**`,
    won
      ? `- Good entry at $${trade.entryPrice.toLocaleString()}. ${rrActual > 1.5 ? "Excellent R:R ratio." : "Acceptable R:R."}`
      : `- Entry at $${trade.entryPrice.toLocaleString()} was ${rrActual < 0.5 ? "too early — signal was not yet confirmed" : "within range, but market moved against"}.`,
    `- Regime was ${ctx.regime}${ctx.regime === "CRISIS" ? " — difficult environment for trades" : ""}.`,
    "",
    `**Recommendation:**`,
    won
      ? `- Keep it up! ${rrActual > 2 ? "Take-profit level was well chosen." : "Consider larger TP targets for better R:R."}`
      : `- ${ctx.oodScore > 0.5 ? "OOD score was high — better to wait in such situations." : "Check signal confidence before next trade."}`,
  ].join("\n");
}
