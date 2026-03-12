// =============================================================================
// src/components/dashboard/market-pulse.tsx — Market Pulse Summary Card
//
// Fear & Greed gauge with 7-day history sparkline, BTC dominance (real),
// momentum and volatility from live price history.
// =============================================================================

"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { MetricTooltip } from "@/components/ui/metric-tooltip";
import { SentimentGauge } from "./sentiment-gauge";
import type { SentimentResult } from "@/hooks/use-sentiment";
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Minus,
  BarChart3,
} from "lucide-react";

interface MarketPulseProps {
  data: SentimentResult;
}

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

function getDominanceColor(trend: "rising" | "falling" | "stable"): string {
  if (trend === "rising") return "text-orange-400";
  if (trend === "falling") return "text-blue-400";
  return "text-zinc-400";
}

function getDominanceIcon(trend: "rising" | "falling" | "stable") {
  if (trend === "rising")
    return <TrendingUp className="h-3.5 w-3.5 text-orange-400" />;
  if (trend === "falling")
    return <TrendingDown className="h-3.5 w-3.5 text-blue-400" />;
  return <Minus className="h-3.5 w-3.5 text-zinc-400" />;
}

function getDominanceLabel(
  trend: "rising" | "falling" | "stable",
  value: number | null
): string {
  const pct = value !== null ? `${value.toFixed(1)}%` : "";
  if (trend === "rising") return pct ? `${pct} ↑` : "Rising";
  if (trend === "falling") return pct ? `${pct} ↓` : "Falling";
  return pct || "Stable";
}

/** Mini sparkline for F&G 7-day history */
function FearGreedHistory({ data }: { data: number[] }) {
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

  // Color based on latest value
  const latest = data[data.length - 1];
  const color =
    latest <= 25
      ? "#ef4444"
      : latest <= 45
        ? "#f97316"
        : latest <= 55
          ? "#eab308"
          : latest <= 75
            ? "#84cc16"
            : "#22c55e";

  return (
    <div className="flex items-center gap-2">
      <span className="text-[9px] text-muted-foreground whitespace-nowrap">7d</span>
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
        {/* Dot on latest value */}
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

export function MarketPulse({ data }: MarketPulseProps) {
  const { sentiment, momentum, volatility, btcDominance } = data;

  return (
    <Card className="bg-card/50 border-border/50">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          <Activity className="h-4 w-4" />
          Market Sentiment
          {sentiment.loading ? (
            <Skeleton className="ml-auto h-4 w-12" />
          ) : sentiment.error ? (
            <Badge
              variant="outline"
              className="ml-auto text-[10px] text-yellow-400 border-yellow-500/30"
            >
              Synthetic
            </Badge>
          ) : (
            <Badge
              variant="outline"
              className="ml-auto text-[10px] text-green-400 border-green-500/30"
            >
              Live
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="pb-4">
        <div className="flex flex-col items-center gap-3">
          {/* Gauge */}
          <MetricTooltip term="Fear & Greed">
            <SentimentGauge
              value={sentiment.value}
              classification={sentiment.classification}
              size={160}
              loading={sentiment.loading}
            />
          </MetricTooltip>

          {/* 7-day F&G history sparkline */}
          {sentiment.history.length >= 2 && (
            <FearGreedHistory data={sentiment.history} />
          )}

          {/* Indicator Grid */}
          <div className="grid grid-cols-3 gap-2 w-full mt-1">
            {/* Momentum */}
            <MetricTooltip term="Momentum">
              <div className="rounded-lg bg-background/50 p-2 text-center">
                {sentiment.loading ? (
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

            {/* BTC Dominance */}
            <MetricTooltip term="BTC Dominance">
              <div className="rounded-lg bg-background/50 p-2 text-center">
                {sentiment.loading ? (
                  <Skeleton className="h-8 w-full" />
                ) : (
                  <>
                    <div className="flex items-center justify-center gap-1 mb-0.5">
                      {getDominanceIcon(btcDominance.trend)}
                      <span className="text-[10px] text-muted-foreground">
                        BTC Dom.
                      </span>
                    </div>
                    <div
                      className={`text-xs font-semibold ${getDominanceColor(btcDominance.trend)}`}
                    >
                      {getDominanceLabel(btcDominance.trend, btcDominance.value)}
                    </div>
                  </>
                )}
              </div>
            </MetricTooltip>

            {/* Volatility */}
            <MetricTooltip term="Volatility">
              <div className="rounded-lg bg-background/50 p-2 text-center">
                {sentiment.loading ? (
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
      </CardContent>
    </Card>
  );
}
