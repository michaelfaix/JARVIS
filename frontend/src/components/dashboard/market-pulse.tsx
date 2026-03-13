// =============================================================================
// src/components/dashboard/market-pulse.tsx — Market Pulse (HUD)
// =============================================================================

"use client";

import React from "react";
import { HudPanel } from "@/components/ui/hud-panel";
import { Skeleton } from "@/components/ui/skeleton";
import { MetricTooltip } from "@/components/ui/metric-tooltip";
import { SentimentGauge } from "./sentiment-gauge";
import type {
  SentimentResult,
  MarketTab,
  MarketSentiment,
} from "@/hooks/use-sentiment";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  BarChart3,
  Link2,
  Unlink,
} from "lucide-react";

interface MarketPulseProps {
  data: SentimentResult;
}

function MomentumIcon({ label }: { label: string }) {
  if (label.includes("Bullish"))
    return <TrendingUp className="h-3 w-3 text-hud-green" />;
  if (label.includes("Bearish"))
    return <TrendingDown className="h-3 w-3 text-hud-red" />;
  return <Minus className="h-3 w-3 text-hud-amber" />;
}

function getMomentumColor(label: string): string {
  if (label.includes("Strong Bullish")) return "text-hud-green";
  if (label.includes("Bullish")) return "text-hud-green/80";
  if (label.includes("Strong Bearish")) return "text-hud-red";
  if (label.includes("Bearish")) return "text-hud-red/80";
  return "text-hud-amber";
}

function getVolatilityColor(label: string): string {
  if (label === "High") return "text-hud-red";
  if (label === "Medium") return "text-hud-amber";
  return "text-hud-green";
}

function TrendIcon({ trend }: { trend: "rising" | "falling" | "stable" }) {
  if (trend === "rising") return <TrendingUp className="h-3 w-3" />;
  if (trend === "falling") return <TrendingDown className="h-3 w-3" />;
  return <Minus className="h-3 w-3" />;
}

function fgColor(value: number): string {
  if (value <= 25) return "#ff4466";
  if (value <= 45) return "#ffaa00";
  if (value <= 55) return "#ffaa00";
  if (value <= 75) return "#00e5a0";
  return "#00e5a0";
}

function HistorySparkline({ data, label }: { data: number[]; label?: string }) {
  if (data.length < 2) return null;
  const w = 100;
  const h = 20;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const points = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * w;
      const y = h - ((v - min) / range) * (h - 2) - 1;
      return `${x},${y}`;
    })
    .join(" ");
  const latest = data[data.length - 1];
  const color = fgColor(latest);

  return (
    <div className="flex items-center gap-1.5">
      <span className="text-[8px] font-mono text-muted-foreground/50">{label ?? "7d"}</span>
      <svg width={w} height={h} className="shrink-0">
        <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" opacity={0.7} />
        <circle cx={w} cy={h - ((latest - min) / range) * (h - 2) - 1} r="2" fill={color} />
      </svg>
    </div>
  );
}

const TABS: { key: MarketTab; label: string }[] = [
  { key: "crypto", label: "Crypto" },
  { key: "stocks", label: "Stocks" },
  { key: "commodities", label: "Commod." },
];

function TabContent({ market }: { market: MarketSentiment }) {
  const { sentiment, momentum, volatility, extraLabel, extraValue, extraColor, extraTrend } = market;
  const loading = sentiment.loading;

  return (
    <div className="flex flex-col items-center gap-2">
      <MetricTooltip term="Fear & Greed">
        <SentimentGauge
          value={sentiment.value}
          classification={sentiment.classification}
          size={120}
          loading={loading}
        />
      </MetricTooltip>

      {sentiment.history.length >= 2 && <HistorySparkline data={sentiment.history} />}

      <div className="grid grid-cols-3 gap-1.5 w-full">
        <MetricTooltip term="Momentum">
          <div className="rounded bg-hud-bg/60 border border-hud-border/30 p-1.5 text-center">
            {loading ? <Skeleton className="h-6 w-full" /> : (
              <>
                <div className="flex items-center justify-center gap-0.5 mb-0.5">
                  <MomentumIcon label={momentum.label} />
                  <span className="text-[8px] font-mono text-muted-foreground/60">Mom.</span>
                </div>
                <div className={`text-[10px] font-mono font-semibold ${getMomentumColor(momentum.label)}`}>
                  {momentum.label}
                </div>
              </>
            )}
          </div>
        </MetricTooltip>

        <MetricTooltip term={extraLabel}>
          <div className="rounded bg-hud-bg/60 border border-hud-border/30 p-1.5 text-center">
            {loading ? <Skeleton className="h-6 w-full" /> : (
              <>
                <div className="flex items-center justify-center gap-0.5 mb-0.5">
                  <span className={extraColor}><TrendIcon trend={extraTrend} /></span>
                  <span className="text-[8px] font-mono text-muted-foreground/60">{extraLabel}</span>
                </div>
                <div className={`text-[10px] font-mono font-semibold ${extraColor}`}>{extraValue}</div>
              </>
            )}
          </div>
        </MetricTooltip>

        <MetricTooltip term="Volatility">
          <div className="rounded bg-hud-bg/60 border border-hud-border/30 p-1.5 text-center">
            {loading ? <Skeleton className="h-6 w-full" /> : (
              <>
                <div className="flex items-center justify-center gap-0.5 mb-0.5">
                  <BarChart3 className={`h-3 w-3 ${getVolatilityColor(volatility.label)}`} />
                  <span className="text-[8px] font-mono text-muted-foreground/60">Vol.</span>
                </div>
                <div className={`text-[10px] font-mono font-semibold ${getVolatilityColor(volatility.label)}`}>
                  {volatility.label}
                </div>
              </>
            )}
          </div>
        </MetricTooltip>
      </div>
    </div>
  );
}

export function MarketPulse({ data }: MarketPulseProps) {
  const { activeTab, setActiveTab, correlation } = data;
  const market = data[activeTab];
  return (
    <HudPanel title="Market Sentiment">
      <div className="p-2.5 space-y-2">
        {/* Tab Switcher */}
        <div className="flex rounded bg-hud-bg/60 p-0.5">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex-1 py-0.5 rounded text-[9px] font-mono transition-colors ${
                activeTab === tab.key
                  ? "bg-hud-cyan/15 text-hud-cyan"
                  : "text-muted-foreground hover:text-hud-cyan"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <TabContent market={market} />

        {/* Correlation Badge */}
        {correlation && (
          <div className={`flex items-center justify-center gap-1 text-[9px] font-mono rounded py-0.5 ${
            correlation.value > 0
              ? "bg-purple-500/10 text-purple-400"
              : "bg-orange-500/10 text-orange-400"
          }`}>
            {correlation.value > 0 ? <Link2 className="h-2.5 w-2.5" /> : <Unlink className="h-2.5 w-2.5" />}
            {correlation.label}
          </div>
        )}
      </div>
    </HudPanel>
  );
}
