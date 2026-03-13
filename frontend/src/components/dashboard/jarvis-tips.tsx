// =============================================================================
// src/components/dashboard/jarvis-tips.tsx — JARVIS Tips Widget
//
// Contextual tips based on FAS regime, ECE calibration, OOD detection,
// sentiment, and strategy selection. Shows "Why?" explanations.
// =============================================================================

"use client";

import { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Lightbulb,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  Shield,
  TrendingUp,
  Zap,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Tip {
  id: string;
  text: string;
  why: string;
  severity: "info" | "warning" | "critical";
  icon: typeof Lightbulb;
}

interface JarvisTipsProps {
  regime: string | null;
  ece: number;
  oodScore: number;
  metaUncertainty: number;
  sentiment: number | null; // -1 to 1
  strategy: string;
}

// ---------------------------------------------------------------------------
// Tip generation logic (FAS-based)
// ---------------------------------------------------------------------------

function generateTips({
  regime,
  ece,
  oodScore,
  metaUncertainty,
  sentiment,
  strategy,
}: JarvisTipsProps): Tip[] {
  const tips: Tip[] = [];

  // --- Regime-based tips ---
  if (regime === "CRISIS") {
    tips.push({
      id: "regime-crisis",
      text: "CRISIS regime detected — reduce position sizes by 50% or switch to defensive assets (GLD, SPY puts).",
      why: "FAS Phase 6A classifies current market conditions as CRISIS. Historical drawdowns in this regime average 15-30%.",
      severity: "critical",
      icon: AlertTriangle,
    });
  } else if (regime === "RISK_OFF") {
    tips.push({
      id: "regime-riskoff",
      text: "RISK_OFF regime — favor mean reversion and defensive strategies. Tighten stop losses.",
      why: "FAS detects elevated uncertainty. Momentum strategies underperform in risk-off environments by ~40%.",
      severity: "warning",
      icon: Shield,
    });
  } else if (regime === "RISK_ON") {
    tips.push({
      id: "regime-riskon",
      text: "RISK_ON regime — ideal for trend following and momentum strategies with wider targets.",
      why: "FAS confirms low uncertainty and strong trend conditions. Historically optimal for directional trades.",
      severity: "info",
      icon: TrendingUp,
    });
  } else if (regime === "TRANSITION") {
    tips.push({
      id: "regime-transition",
      text: "Market in TRANSITION — wait for regime confirmation before opening new positions.",
      why: "FAS signals regime change in progress. Signals are unreliable during transitions (accuracy drops ~25%).",
      severity: "warning",
      icon: Zap,
    });
  }

  // --- ECE calibration gate ---
  if (ece > 0.05) {
    tips.push({
      id: "ece-high",
      text: `Model calibration poor (ECE: ${(ece * 100).toFixed(1)}%) — treat confidence scores with caution.`,
      why: "FAS requires ECE < 5% for reliable predictions. Current calibration means confidence values may be misleading.",
      severity: "warning",
      icon: AlertTriangle,
    });
  }

  // --- OOD detection ---
  if (oodScore > 0.5) {
    tips.push({
      id: "ood-high",
      text: "Out-of-Distribution data detected — current market conditions differ from training data.",
      why: `OOD score ${(oodScore * 100).toFixed(0)}% exceeds threshold. Model predictions may be unreliable for unseen market patterns.`,
      severity: oodScore > 0.8 ? "critical" : "warning",
      icon: AlertTriangle,
    });
  }

  // --- Meta-uncertainty ---
  if (metaUncertainty > 0.3) {
    tips.push({
      id: "meta-uncertain",
      text: "High meta-uncertainty — JARVIS is uncertain about its own uncertainty estimates.",
      why: "When meta-uncertainty exceeds 30%, the system's risk assessment itself becomes unreliable. Use manual risk management.",
      severity: "warning",
      icon: Shield,
    });
  }

  // --- Sentiment-strategy alignment ---
  if (sentiment !== null) {
    if (sentiment < -0.3 && (strategy === "momentum" || strategy === "trend_following" || strategy === "breakout")) {
      tips.push({
        id: "sentiment-mismatch",
        text: "Bearish sentiment conflicts with bullish strategy — consider mean reversion or reducing exposure.",
        why: `Market sentiment is ${(sentiment * 100).toFixed(0)}% bearish. ${strategy} strategies typically need neutral-to-positive sentiment for optimal performance.`,
        severity: "warning",
        icon: Lightbulb,
      });
    } else if (sentiment > 0.5 && strategy === "mean_reversion") {
      tips.push({
        id: "sentiment-strong-trend",
        text: "Strong bullish sentiment detected — mean reversion may face headwinds. Consider trend following.",
        why: "When sentiment exceeds +50%, mean reversion signals tend to produce false reversals as momentum overrides.",
        severity: "info",
        icon: Lightbulb,
      });
    }
  }

  // --- Strategy-specific tips ---
  if (strategy === "custom") {
    tips.push({
      id: "custom-tip",
      text: "Custom strategy active — backtest thoroughly before live trading. Check rule logic for edge cases.",
      why: "Custom rules bypass JARVIS's optimized presets. Without backtesting, risk of overfitting or logic errors is high.",
      severity: "info",
      icon: Lightbulb,
    });
  }

  // --- Default tip if none generated ---
  if (tips.length === 0) {
    tips.push({
      id: "default",
      text: "All systems nominal — current strategy aligns with market conditions.",
      why: "FAS regime, calibration, and sentiment are all within optimal ranges for your selected strategy.",
      severity: "info",
      icon: TrendingUp,
    });
  }

  return tips;
}

// ---------------------------------------------------------------------------
// Severity colors
// ---------------------------------------------------------------------------

const SEVERITY_STYLES = {
  info: {
    bg: "bg-blue-500/10",
    border: "border-blue-500/20",
    text: "text-blue-400",
    badge: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  },
  warning: {
    bg: "bg-yellow-500/10",
    border: "border-yellow-500/20",
    text: "text-yellow-400",
    badge: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  },
  critical: {
    bg: "bg-red-500/10",
    border: "border-red-500/20",
    text: "text-red-400",
    badge: "bg-red-500/20 text-red-400 border-red-500/30",
  },
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function JarvisTips(props: JarvisTipsProps) {
  const tips = useMemo(() => generateTips(props), [props]);
  const [expandedTip, setExpandedTip] = useState<string | null>(null);

  const hasCritical = tips.some((t) => t.severity === "critical");
  const hasWarning = tips.some((t) => t.severity === "warning");

  return (
    <Card className="bg-card/50 border-border/50">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          <Lightbulb className={`h-4 w-4 ${hasCritical ? "text-red-400" : hasWarning ? "text-yellow-400" : "text-blue-400"}`} />
          JARVIS Tips
          <Badge className={`ml-1 text-[9px] ${hasCritical ? SEVERITY_STYLES.critical.badge : hasWarning ? SEVERITY_STYLES.warning.badge : SEVERITY_STYLES.info.badge}`}>
            {tips.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 pb-3">
        {tips.map((tip) => {
          const s = SEVERITY_STYLES[tip.severity];
          const isExpanded = expandedTip === tip.id;
          return (
            <div
              key={tip.id}
              className={`rounded-lg ${s.bg} border ${s.border} px-3 py-2`}
            >
              <button
                onClick={() => setExpandedTip(isExpanded ? null : tip.id)}
                className="w-full flex items-start gap-2 text-left"
              >
                <tip.icon className={`h-3.5 w-3.5 mt-0.5 shrink-0 ${s.text}`} />
                <span className="text-[11px] text-white/90 flex-1 leading-relaxed">
                  {tip.text}
                </span>
                {isExpanded ? (
                  <ChevronUp className="h-3 w-3 text-muted-foreground shrink-0 mt-0.5" />
                ) : (
                  <ChevronDown className="h-3 w-3 text-muted-foreground shrink-0 mt-0.5" />
                )}
              </button>
              {isExpanded && (
                <div className="mt-2 ml-5.5 pl-1 border-l-2 border-border/30">
                  <span className="text-[10px] text-muted-foreground font-medium">Why?</span>
                  <p className="text-[10px] text-muted-foreground leading-relaxed mt-0.5">
                    {tip.why}
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
