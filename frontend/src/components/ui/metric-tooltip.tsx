// =============================================================================
// src/components/ui/metric-tooltip.tsx — Hover tooltip for trading metrics
// =============================================================================

"use client";

import { useState, useRef, useCallback, type ReactNode } from "react";
import { HelpCircle } from "lucide-react";

interface MetricTooltipProps {
  term: string;
  children?: ReactNode;
}

const GLOSSARY: Record<string, string> = {
  "ECE": "Expected Calibration Error — measures how well predicted probabilities match actual outcomes. Lower is better. <0.05 = well calibrated.",
  "OOD": "Out-of-Distribution Score — detects when input data differs from training data. High OOD means the model is uncertain about the current market regime.",
  "Meta-U": "Meta-Uncertainty — quantifies the model's uncertainty about its own uncertainty estimates. High values trigger conservative trading modes.",
  "Calibration": "How accurate the model's confidence scores are. 100% means predicted probabilities perfectly match real outcomes.",
  "Confidence": "The model's self-assessed certainty in its predictions. Higher confidence = stronger signal conviction.",
  "Stability": "Model output consistency over time. High stability means predictions don't flip-flop between updates.",
  "Data Quality": "Freshness and completeness of input data. Drops when feeds are delayed, missing, or corrupted.",
  "Regime": "How well the model adapts to the current market regime (Risk On, Risk Off, Crisis, Transition).",
  "Quality Score": "Composite score (0-100) combining Calibration, Confidence, Stability, Data Quality, and Regime components.",
  "Market Regime": "Current market state detected by JARVIS. RISK_ON = bullish conditions, RISK_OFF = caution, CRISIS = defensive mode, TRANSITION = regime shift in progress.",
  "Risk On": "Bullish market conditions — the model has high confidence and market indicators are favorable. Full signal generation active.",
  "Risk Off": "Cautious conditions — elevated uncertainty or bearish signals detected. Position sizes reduced automatically.",
  "Crisis": "Emergency mode — extreme uncertainty or market stress detected. Only monitoring, no new signals generated.",
  "Transition": "Regime shift in progress — the market is moving between states. Signals may be less reliable during transitions.",
  "Drawdown": "Maximum portfolio value decline from peak. Measures worst-case loss exposure. >5% triggers risk warnings.",
  "Win Rate": "Percentage of closed trades that were profitable. Above 50% generally indicates a profitable strategy.",
  "Sharpe": "Risk-adjusted return metric. Measures excess return per unit of volatility. >1.0 is good, >2.0 is excellent.",
  "Fear & Greed": "Crypto market sentiment index (0-100). 0 = Extreme Fear (buying opportunity), 100 = Extreme Greed (sell signal).",
  "Momentum": "Directional price strength across tracked assets. Bullish = prices rising, Bearish = prices falling.",
  "Volatility": "Price fluctuation intensity. High volatility = larger price swings = higher risk and opportunity.",
  "BTC Dominance": "Bitcoin's share of total crypto market cap. Rising = risk-off (money flows to BTC), Falling = altcoin season.",
  "Predictions": "Whether the JARVIS prediction engine is actively generating signals. Disabled during Crisis or maintenance modes.",
  "System Mode": "JARVIS degradation level. NORMAL = full operation. Higher modes progressively reduce risk exposure.",
};

export function MetricTooltip({ term, children }: MetricTooltipProps) {
  const [visible, setVisible] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();

  const show = useCallback(() => {
    clearTimeout(timeoutRef.current);
    setVisible(true);
  }, []);

  const hide = useCallback(() => {
    timeoutRef.current = setTimeout(() => setVisible(false), 150);
  }, []);

  const explanation = GLOSSARY[term];
  if (!explanation) return <>{children}</>;

  return (
    <span
      className="relative inline-flex items-center gap-1 cursor-help"
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
      tabIndex={0}
    >
      {children}
      <HelpCircle className="h-3 w-3 text-muted-foreground/50 shrink-0" />
      {visible && (
        <span className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 rounded-lg bg-popover border border-border/50 px-3 py-2 text-xs text-popover-foreground shadow-lg leading-relaxed pointer-events-none">
          <span className="font-semibold text-white">{term}</span>
          <br />
          {explanation}
        </span>
      )}
    </span>
  );
}
