// =============================================================================
// src/components/dashboard/market-pulse.tsx — Multi-Market Pulse Card
//
// Tab-switchable: Crypto | Stocks | Commodities
// Each tab: F&G gauge + 7d sparkline + momentum + extra indicator + volatility
// Correlation badge when crypto & stocks move together/apart.
// =============================================================================

"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { MetricTooltip } from "@/components/ui/metric-tooltip";
import { SentimentGauge } from "./sentiment-gauge";
import type {
  SentimentResult,
  MarketTab,
  MarketSentiment,
} from "@/hooks/use-sentiment";
import {
  Activity,
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

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function MomentumIcon({ label }: { label: string }) {
  if (label.includes("Bullish"))
    return <TrendingUp className="h-3.5 w-3.5 text-green-400" />;
  if (label.includes("Bearish"))
    return <TrendingDown className="h-3.5 w-3.5 text-red-400" />;
  return <Minus className="h-3.5 w-3.5 text-yellow-400" />;
}

function getMomentumColor(label: string): string {
  if (label.includes("Strong Bullish")) return "text-green-400";
  if (label.includes("Bullish")) return "text-green-300";
  if (label.includes("Strong Bearish")) return "text-red-400";
  if (label.includes("Bearish")) return "text-red-300";
  return "text-yellow-400";
}

function getVolatilityColor(label: string): string {
  if (label === "High") return "text-red-400";
  if (label === "Medium") return "text-yellow-400";
  return "text-green-400";
}

function TrendIcon({ trend }: { trend: "rising" | "falling" | "stable" }) {
  if (trend === "rising")
    return <TrendingUp className="h-3.5 w-3.5" />;
  if (trend === "falling")
    return <TrendingDown className="h-3.5 w-3.5" />;
  return <Minus className="h-3.5 w-3.5" />;
}

function fgColor(value: number): string {
  if (value <= 25) return "#ef4444";
  if (value <= 45) return "#f97316";
  if (value <= 55) return "#eab308";
  if (value <= 75) return "#84cc16";
  return "#22c55e";
}

// ---------------------------------------------------------------------------
// Mini sparkline
// ---------------------------------------------------------------------------

function HistorySparkline({ data, label }: { data: number[]; label?: string }) {
  if (data.length < 2) return null;
  const w = 120;
  const h = 24;
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
    <div className="flex items-center gap-2">
      <span className="text-[9px] text-muted-foreground whitespace-nowrap">
        {label ?? "7d"}
      </span>
      <svg width={w} height={h} className="shrink-0">
        <polyline
          points={points}
          fill="none"
          stroke={color}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity={0.8}
        />
        <circle
          cx={w}
          cy={h - ((latest - min) / range) * (h - 2) - 1}
          r="2.5"
          fill={color}
        />
      </svg>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab config
// ---------------------------------------------------------------------------

const TABS: { key: MarketTab; label: string; tooltip: string }[] = [
  { key: "crypto", label: "Crypto", tooltip: "Fear & Greed" },
  { key: "stocks", label: "Stocks", tooltip: "Fear & Greed" },
  { key: "commodities", label: "Commodities", tooltip: "Fear & Greed" },
];

// ---------------------------------------------------------------------------
// Per-tab content
// ---------------------------------------------------------------------------

function TabContent({ market }: { market: MarketSentiment }) {
  const { sentiment, momentum, volatility, extraLabel, extraValue, extraColor, extraTrend } =
    market;

  const loading = sentiment.loading;

  return (
    <div className="flex flex-col items-center gap-3">
      {/* Gauge */}
      <MetricTooltip term="Fear & Greed">
        <SentimentGauge
          value={sentiment.value}
          classification={sentiment.classification}
          size={150}
          loading={loading}
        />
      </MetricTooltip>

      {/* History sparkline */}
      {sentiment.history.length >= 2 && (
        <HistorySparkline data={sentiment.history} />
      )}

      {/* Indicator Grid */}
      <div className="grid grid-cols-3 gap-2 w-full mt-1">
        {/* Momentum */}
        <MetricTooltip term="Momentum">
          <div className="rounded-lg bg-background/50 p-2 text-center">
            {loading ? (
              <Skeleton className="h-8 w-full" />
            ) : (
              <>
                <div className="flex items-center justify-center gap-1 mb-0.5">
                  <MomentumIcon label={momentum.label} />
                  <span className="text-[10px] text-muted-foreground">
                    Momentum
                  </span>
                </div>
                <div
                  className={`text-xs font-semibold ${getMomentumColor(momentum.label)}`}
                >
                  {momentum.label}
                </div>
              </>
            )}
          </div>
        </MetricTooltip>

        {/* Extra Indicator (BTC Dom / VIX / Gold Trend) */}
        <MetricTooltip term={extraLabel}>
          <div className="rounded-lg bg-background/50 p-2 text-center">
            {loading ? (
              <Skeleton className="h-8 w-full" />
            ) : (
              <>
                <div className="flex items-center justify-center gap-1 mb-0.5">
                  <span className={extraColor}>
                    <TrendIcon trend={extraTrend} />
                  </span>
                  <span className="text-[10px] text-muted-foreground">
                    {extraLabel}
                  </span>
                </div>
                <div className={`text-xs font-semibold ${extraColor}`}>
                  {extraValue}
                </div>
              </>
            )}
          </div>
        </MetricTooltip>

        {/* Volatility */}
        <MetricTooltip term="Volatility">
          <div className="rounded-lg bg-background/50 p-2 text-center">
            {loading ? (
              <Skeleton className="h-8 w-full" />
            ) : (
              <>
                <div className="flex items-center justify-center gap-1 mb-0.5">
                  <BarChart3
                    className={`h-3.5 w-3.5 ${getVolatilityColor(volatility.label)}`}
                  />
                  <span className="text-[10px] text-muted-foreground">
                    Volatility
                  </span>
                </div>
                <div
                  className={`text-xs font-semibold ${getVolatilityColor(volatility.label)}`}
                >
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

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

export function MarketPulse({ data }: MarketPulseProps) {
  const { activeTab, setActiveTab, correlation } = data;
  const market = data[activeTab];
  const isLive = !market.sentiment.error && !market.sentiment.loading;
  const isSynthetic = !!market.sentiment.error && !market.sentiment.loading;

  return (
    <Card className="bg-card/50 border-border/50">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          <Activity className="h-4 w-4" />
          Market Sentiment
          {market.sentiment.loading ? (
            <Skeleton className="ml-auto h-4 w-12" />
          ) : isSynthetic ? (
            <Badge
              variant="outline"
              className="ml-auto text-[10px] text-yellow-400 border-yellow-500/30"
            >
              Synthetic
            </Badge>
          ) : isLive ? (
            <Badge
              variant="outline"
              className="ml-auto text-[10px] text-green-400 border-green-500/30"
            >
              Live
            </Badge>
          ) : null}
        </CardTitle>
      </CardHeader>
      <CardContent className="pb-4 space-y-3">
        {/* Tab Switcher */}
        <div className="flex rounded-lg bg-background/50 p-0.5">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex-1 py-1 rounded-md text-[11px] font-medium transition-colors ${
                activeTab === tab.key
                  ? "bg-blue-600/20 text-blue-400"
                  : "text-muted-foreground hover:text-white"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <TabContent market={market} />

        {/* Correlation Badge */}
        {correlation && (
          <div
            className={`flex items-center justify-center gap-1.5 text-[10px] rounded-md py-1 ${
              correlation.value > 0
                ? "bg-purple-500/10 text-purple-400"
                : "bg-orange-500/10 text-orange-400"
            }`}
          >
            {correlation.value > 0 ? (
              <Link2 className="h-3 w-3" />
            ) : (
              <Unlink className="h-3 w-3" />
            )}
            {correlation.label}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
