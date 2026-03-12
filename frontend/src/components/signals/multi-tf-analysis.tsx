"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Minus, BarChart3 } from "lucide-react";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface MultiTfAnalysisProps {
  asset: string;
  currentPrice: number;
}

type Direction = "LONG" | "SHORT" | "NEUTRAL";
type Trend = "Bullish" | "Bearish" | "Ranging";

interface TimeframeSignal {
  tf: string;
  direction: Direction;
  strength: number; // 0-100
  trend: Trend;
  keyLevel: number;
  keyLevelType: "Support" | "Resistance";
}

// ---------------------------------------------------------------------------
// Deterministic seed helpers
// ---------------------------------------------------------------------------

function hashCode(str: string): number {
  let hash = 5381;
  for (let i = 0; i < str.length; i++) {
    hash = (hash * 33) ^ str.charCodeAt(i);
  }
  return hash >>> 0;
}

/** Simple seeded PRNG (mulberry32) */
function seededRandom(seed: number): () => number {
  let s = seed | 0;
  return () => {
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ---------------------------------------------------------------------------
// Data generation
// ---------------------------------------------------------------------------

const TIMEFRAMES = ["1m", "5m", "15m", "1H", "4H", "1D", "1W"] as const;

function generateSignals(
  asset: string,
  currentPrice: number
): TimeframeSignal[] {
  const seed = hashCode(asset);
  const rand = seededRandom(seed);

  return TIMEFRAMES.map((tf) => {
    const r = rand();
    const direction: Direction =
      r < 0.4 ? "LONG" : r < 0.75 ? "SHORT" : "NEUTRAL";

    const strength = Math.round(rand() * 100);

    const trendR = rand();
    const trend: Trend =
      trendR < 0.4 ? "Bullish" : trendR < 0.75 ? "Bearish" : "Ranging";

    const isSupport = rand() > 0.5;
    const offset = currentPrice * (0.005 + rand() * 0.03);
    const keyLevel = isSupport
      ? currentPrice - offset
      : currentPrice + offset;

    return {
      tf,
      direction,
      strength,
      trend,
      keyLevel: Math.round(keyLevel * 100) / 100,
      keyLevelType: isSupport ? "Support" : "Resistance",
    };
  });
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function DirectionIcon({ direction }: { direction: Direction }) {
  if (direction === "LONG") {
    return <TrendingUp className="h-4 w-4 text-emerald-500" />;
  }
  if (direction === "SHORT") {
    return <TrendingDown className="h-4 w-4 text-red-500" />;
  }
  return <Minus className="h-4 w-4 text-muted-foreground" />;
}

function DirectionArrow({ direction }: { direction: Direction }) {
  if (direction === "LONG") {
    return <span className="text-lg leading-none text-emerald-500">&#8593;</span>;
  }
  if (direction === "SHORT") {
    return <span className="text-lg leading-none text-red-500">&#8595;</span>;
  }
  return <span className="text-lg leading-none text-muted-foreground">&#8594;</span>;
}

function StrengthBar({ value }: { value: number }) {
  const color =
    value >= 70
      ? "bg-emerald-500"
      : value >= 40
        ? "bg-yellow-500"
        : "bg-red-500";

  return (
    <div className="h-1.5 w-full rounded-full bg-muted">
      <div
        className={cn("h-full rounded-full transition-all", color)}
        style={{ width: `${value}%` }}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function MultiTfAnalysis({
  asset,
  currentPrice,
}: MultiTfAnalysisProps) {
  const signals = React.useMemo(
    () => generateSignals(asset, currentPrice),
    [asset, currentPrice]
  );

  // Confluence calculation
  const longCount = signals.filter((s) => s.direction === "LONG").length;
  const shortCount = signals.filter((s) => s.direction === "SHORT").length;
  const dominantDirection = longCount >= shortCount ? "LONG" : "SHORT";
  const dominantCount = Math.max(longCount, shortCount);
  const confluencePercent = Math.round((dominantCount / signals.length) * 100);

  const confluenceColor =
    confluencePercent >= 70
      ? "text-emerald-500"
      : confluencePercent >= 40
        ? "text-yellow-500"
        : "text-red-500";

  const confluenceBg =
    confluencePercent >= 70
      ? "bg-emerald-500/10 border-emerald-500/30"
      : confluencePercent >= 40
        ? "bg-yellow-500/10 border-yellow-500/30"
        : "bg-red-500/10 border-red-500/30";

  const biasLabel =
    dominantDirection === "LONG" ? "Bullish" : "Bearish";

  const summaryText =
    confluencePercent >= 70
      ? `Strong ${biasLabel} Bias`
      : confluencePercent >= 40
        ? "Mixed - Exercise Caution"
        : "Conflicting Signals - No Clear Edge";

  const summaryBadgeVariant =
    confluencePercent >= 70
      ? "default"
      : confluencePercent >= 40
        ? "secondary"
        : "destructive";

  // Highlight the 1H timeframe as "current" by default
  const activeTf = "1H";

  return (
    <Card className="bg-card/50 border-border/50">
      <CardHeader className="p-4 pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-sm font-semibold">
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
            Multi-Timeframe Analysis
          </CardTitle>
          <Badge variant="outline" className="text-xs font-mono">
            {asset}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="p-4 pt-2 space-y-3">
        {/* Confluence Score */}
        <div
          className={cn(
            "flex items-center justify-between rounded-md border px-3 py-2",
            confluenceBg
          )}
        >
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Confluence</span>
            <span className={cn("text-sm font-bold", confluenceColor)}>
              {dominantCount}/{signals.length} {biasLabel}
            </span>
          </div>
          <span className={cn("text-lg font-bold tabular-nums", confluenceColor)}>
            {confluencePercent}%
          </span>
        </div>

        {/* Timeframe Grid */}
        <div className="overflow-x-auto -mx-1 px-1 pb-1">
          <div className="grid grid-cols-7 gap-1.5 min-w-[560px]">
            {signals.map((signal) => {
              const isActive = signal.tf === activeTf;
              return (
                <div
                  key={signal.tf}
                  className={cn(
                    "flex flex-col items-center gap-1 rounded-md border p-2 transition-colors",
                    isActive
                      ? "border-primary/50 bg-primary/5 ring-1 ring-primary/20"
                      : "border-border/50 bg-card/30"
                  )}
                >
                  {/* TF Label */}
                  <span
                    className={cn(
                      "text-[10px] font-semibold uppercase tracking-wider",
                      isActive ? "text-primary" : "text-muted-foreground"
                    )}
                  >
                    {signal.tf}
                  </span>

                  {/* Direction Arrow */}
                  <DirectionArrow direction={signal.direction} />

                  {/* Direction Text */}
                  <span
                    className={cn(
                      "text-[10px] font-medium",
                      signal.direction === "LONG"
                        ? "text-emerald-500"
                        : signal.direction === "SHORT"
                          ? "text-red-500"
                          : "text-muted-foreground"
                    )}
                  >
                    {signal.direction}
                  </span>

                  {/* Strength Bar */}
                  <div className="w-full px-0.5">
                    <StrengthBar value={signal.strength} />
                  </div>
                  <span className="text-[10px] tabular-nums text-muted-foreground">
                    {signal.strength}%
                  </span>

                  {/* Trend */}
                  <span
                    className={cn(
                      "text-[10px]",
                      signal.trend === "Bullish"
                        ? "text-emerald-500"
                        : signal.trend === "Bearish"
                          ? "text-red-500"
                          : "text-muted-foreground"
                    )}
                  >
                    {signal.trend}
                  </span>

                  {/* Key Level */}
                  <div className="flex flex-col items-center">
                    <span className="text-[9px] text-muted-foreground">
                      {signal.keyLevelType}
                    </span>
                    <span className="text-[10px] font-mono tabular-nums text-foreground/80">
                      {signal.keyLevel.toLocaleString()}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Summary Row */}
        <div className="flex items-center justify-between rounded-md border border-border/50 bg-muted/30 px-3 py-2">
          <span className="text-xs text-muted-foreground">Overall Bias</span>
          <Badge variant={summaryBadgeVariant as "default" | "secondary" | "destructive"} className="text-xs">
            {confluencePercent >= 70 ? (
              <DirectionIcon direction={dominantDirection} />
            ) : (
              <Minus className="h-3 w-3 mr-1" />
            )}
            <span className="ml-1">{summaryText}</span>
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}
