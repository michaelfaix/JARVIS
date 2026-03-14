// =============================================================================
// src/app/(app)/glossary/page.tsx — Trading Glossar / Glossary
// =============================================================================

"use client";

import { useState } from "react";
import { HudPanel } from "@/components/ui/hud-panel";
import { BookOpen, Search } from "lucide-react";

const GLOSSARY_ENTRIES = [
  { term: "ECE", de: "Expected Calibration Error — misst wie gut vorhergesagte Wahrscheinlichkeiten mit tatsächlichen Ergebnissen übereinstimmen. Niedriger = besser. <0.05 = gut kalibriert.", en: "Expected Calibration Error — measures how well predicted probabilities match actual outcomes. Lower is better. <0.05 = well calibrated." },
  { term: "OOD Score", de: "Out-of-Distribution Score — erkennt wenn aktuelle Marktdaten sich von Trainingsdaten unterscheiden. Hoher OOD = Modell ist unsicher.", en: "Out-of-Distribution Score — detects when input data differs from training data. High OOD = model is uncertain." },
  { term: "Meta-Uncertainty", de: "Meta-Unsicherheit — quantifiziert die Unsicherheit des Modells über seine eigenen Unsicherheitsschätzungen.", en: "Meta-Uncertainty — quantifies the model's uncertainty about its own uncertainty estimates." },
  { term: "Calibration", de: "Wie genau die Konfidenz-Werte des Modells sind. 100% = vorhergesagte Wahrscheinlichkeiten stimmen perfekt.", en: "How accurate the model's confidence scores are. 100% means predicted probabilities perfectly match real outcomes." },
  { term: "Confidence", de: "Selbsteingeschätzte Sicherheit des Modells in seine Vorhersagen. Höhere Konfidenz = stärkeres Signal.", en: "The model's self-assessed certainty in its predictions. Higher = stronger signal conviction." },
  { term: "Quality Score", de: "Composite-Score (0-100) aus Calibration, Confidence, Stability, Data Quality und Regime.", en: "Composite score (0-100) combining Calibration, Confidence, Stability, Data Quality, and Regime." },
  { term: "Market Regime", de: "Aktueller Marktzustand: RISK_ON (bullisch), RISK_OFF (vorsichtig), CRISIS (defensiv), TRANSITION (Wechsel).", en: "Current market state: RISK_ON (bullish), RISK_OFF (cautious), CRISIS (defensive), TRANSITION (shifting)." },
  { term: "Drawdown", de: "Maximaler Wertrückgang vom Höchststand. Misst worst-case Verlustexposition. >5% löst Warnung aus.", en: "Maximum portfolio value decline from peak. >5% triggers risk warnings." },
  { term: "Win Rate", de: "Prozentsatz profitabler geschlossener Trades. Über 50% = profitable Strategie.", en: "Percentage of closed trades that were profitable. Above 50% = profitable strategy." },
  { term: "Sharpe Ratio", de: "Risikoadjustierte Rendite. Misst Überrendite pro Volatilitätseinheit. >1.0 gut, >2.0 exzellent.", en: "Risk-adjusted return. Measures excess return per unit of volatility. >1.0 good, >2.0 excellent." },
  { term: "Profit Factor", de: "Verhältnis Bruttogewinn zu Bruttoverlust. >1.0 = profitabel, >1.5 gut, >2.0 exzellent.", en: "Ratio of gross profits to gross losses. >1.0 = profitable, >1.5 good, >2.0 excellent." },
  { term: "Fear & Greed", de: "Krypto-Sentimentindex (0-100). 0 = extreme Angst (Kaufgelegenheit), 100 = extreme Gier (Verkaufssignal).", en: "Crypto sentiment index (0-100). 0 = extreme fear (buy opportunity), 100 = extreme greed (sell signal)." },
  { term: "Momentum", de: "Richtungsstärke der Preisbewegung. Bullisch = steigende Preise, Bärisch = fallende Preise.", en: "Directional price strength. Bullish = prices rising, Bearish = prices falling." },
  { term: "Volatilität", de: "Intensität der Preisschwankungen. Hoch = größere Schwankungen = höheres Risiko und Chance.", en: "Price fluctuation intensity. High = larger swings = higher risk and opportunity." },
  { term: "RSI", de: "Relative Strength Index (0-100). >70 = überkauft (Verkaufssignal), <30 = überverkauft (Kaufsignal).", en: "Relative Strength Index (0-100). >70 = overbought (sell), <30 = oversold (buy)." },
  { term: "MACD", de: "Moving Average Convergence Divergence — Trendfolge-Indikator. Crossover = Trendwechsel.", en: "Moving Average Convergence Divergence — trend-following indicator. Crossover = trend change." },
  { term: "Bollinger Bands", de: "Volatilitätsbänder um den Durchschnitt. Preis am oberen Band = überkauft, am unteren = überverkauft.", en: "Volatility bands around moving average. Price at upper band = overbought, lower = oversold." },
  { term: "ATR", de: "Average True Range — misst die durchschnittliche Schwankungsbreite. Für Stop-Loss Berechnung.", en: "Average True Range — measures average price range. Used for stop-loss calculation." },
  { term: "Stop Loss (SL)", de: "Automatischer Verlustbegrenzung. Schließt Position wenn Preis unter/über Schwelle fällt.", en: "Automatic loss limit. Closes position when price drops below/above threshold." },
  { term: "Take Profit (TP)", de: "Automatische Gewinnmitnahme. Schließt Position wenn Preis-Ziel erreicht.", en: "Automatic profit taking. Closes position when price target is reached." },
  { term: "R:R (Risk:Reward)", de: "Verhältnis von Risiko zu Gewinnpotential. 1:2 = €1 Risiko für €2 Gewinn. >1:2 empfohlen.", en: "Ratio of risk to potential reward. 1:2 = €1 risk for €2 reward. >1:2 recommended." },
  { term: "Paper Trading", de: "Simulierter Handel mit virtuellem Geld. Kein echtes Kapitalrisiko. Zum Üben und Testen.", en: "Simulated trading with virtual money. No real capital risk. For practice and testing." },
  { term: "Slippage", de: "Preisdifferenz zwischen erwarteter und tatsächlicher Ausführung. Entsteht durch Marktbewegung.", en: "Price difference between expected and actual execution. Caused by market movement." },
  { term: "BTC Dominance", de: "Bitcoins Anteil an der gesamten Krypto-Marktkapitalisierung. Steigend = Risk-Off, Fallend = Altcoin-Saison.", en: "Bitcoin's share of total crypto market cap. Rising = risk-off, Falling = altcoin season." },
  { term: "VIX", de: "Volatilitätsindex — misst erwartete Marktvolatilität. <18 ruhig, 18-25 moderat, >25 hohe Angst.", en: "Volatility Index — measures expected market volatility. <18 calm, 18-25 moderate, >25 high fear." },
  { term: "Position Size", de: "Größe einer Position relativ zum Portfolio. JARVIS empfiehlt basierend auf Konfidenz und Risiko.", en: "Position size relative to portfolio. JARVIS recommends based on confidence and risk." },
  { term: "Regime Detection", de: "JARVIS erkennt automatisch den Marktzustand und passt Strategie und Risiko entsprechend an.", en: "JARVIS automatically detects market state and adjusts strategy and risk accordingly." },
  { term: "Backtesting", de: "Testen einer Strategie auf historischen Daten. Zeigt wie sie in der Vergangenheit performt hätte.", en: "Testing a strategy on historical data. Shows how it would have performed in the past." },
];

export default function GlossaryPage() {
  const [search, setSearch] = useState("");

  const filtered = search
    ? GLOSSARY_ENTRIES.filter(
        (e) =>
          e.term.toLowerCase().includes(search.toLowerCase()) ||
          e.de.toLowerCase().includes(search.toLowerCase())
      )
    : GLOSSARY_ENTRIES;

  return (
    <div className="p-2 sm:p-3 md:p-4 space-y-3 max-w-3xl">
      <HudPanel title="GLOSSAR">
        <div className="p-2.5">
          <div className="flex items-center gap-2 mb-3">
            <BookOpen className="h-4 w-4 text-hud-cyan" />
            <span className="font-mono text-[10px] text-muted-foreground">
              {filtered.length} Begriffe
            </span>
            <div className="flex-1 flex items-center gap-1.5 ml-2">
              <Search className="h-3 w-3 text-muted-foreground" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Suchen..."
                className="flex-1 bg-hud-bg/80 border border-hud-border rounded px-2 py-1 text-[10px] font-mono text-white placeholder:text-muted-foreground/40 focus:outline-none focus:border-hud-cyan/50"
              />
            </div>
          </div>
          <div className="space-y-2">
            {filtered.map((entry) => (
              <div
                key={entry.term}
                className="rounded bg-hud-bg/60 border border-hud-border/20 p-2"
              >
                <div className="font-mono text-[10px] font-bold text-hud-cyan mb-0.5">
                  {entry.term}
                </div>
                <div className="font-mono text-[9px] text-muted-foreground leading-relaxed">
                  {entry.de}
                </div>
              </div>
            ))}
          </div>
        </div>
      </HudPanel>
    </div>
  );
}
