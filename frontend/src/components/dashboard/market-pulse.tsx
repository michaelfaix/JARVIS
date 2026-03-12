// =============================================================================
// src/components/dashboard/market-pulse.tsx — Market Pulse Summary Card
//
// Compact card with Fear & Greed mini-gauge, BTC dominance trend,
// market momentum, and volatility indicators.
// =============================================================================

"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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

function getDominanceIcon(trend: "rising" | "falling" | "stable") {
  if (trend === "rising")
    return <TrendingUp className="h-3.5 w-3.5 text-orange-400" />;
  if (trend === "falling")
    return <TrendingDown className="h-3.5 w-3.5 text-blue-400" />;
  return <Minus className="h-3.5 w-3.5 text-zinc-400" />;
}

function getDominanceColor(trend: "rising" | "falling" | "stable"): string {
  if (trend === "rising") return "text-orange-400";
  if (trend === "falling") return "text-blue-400";
  return "text-zinc-400";
}

function getDominanceLabel(trend: "rising" | "falling" | "stable"): string {
  if (trend === "rising") return "Rising";
  if (trend === "falling") return "Falling";
  return "Stable";
}

export function MarketPulse({ data }: MarketPulseProps) {
  const { sentiment, momentum, volatility, btcDominanceTrend } = data;

  return (
    <Card className="bg-card/50 border-border/50">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          <Activity className="h-4 w-4" />
          Market Sentiment
          {sentiment.error && (
            <Badge
              variant="outline"
              className="ml-auto text-[10px] text-yellow-400 border-yellow-500/30"
            >
              Synthetic
            </Badge>
          )}
          {!sentiment.error && !sentiment.loading && (
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
          <SentimentGauge
            value={sentiment.value}
            classification={sentiment.classification}
            size={160}
            loading={sentiment.loading}
          />

          {/* Indicator Grid */}
          <div className="grid grid-cols-3 gap-2 w-full mt-1">
            {/* Momentum */}
            <div className="rounded-lg bg-background/50 p-2 text-center">
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
            </div>

            {/* BTC Dominance */}
            <div className="rounded-lg bg-background/50 p-2 text-center">
              <div className="flex items-center justify-center gap-1 mb-0.5">
                {getDominanceIcon(btcDominanceTrend)}
                <span className="text-[10px] text-muted-foreground">
                  BTC Dom.
                </span>
              </div>
              <div
                className={`text-xs font-semibold ${getDominanceColor(btcDominanceTrend)}`}
              >
                {getDominanceLabel(btcDominanceTrend)}
              </div>
            </div>

            {/* Volatility */}
            <div className="rounded-lg bg-background/50 p-2 text-center">
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
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
