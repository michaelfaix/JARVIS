// =============================================================================
// src/components/portfolio/trade-stats-dashboard.tsx — Trade Statistics Dashboard
// =============================================================================

"use client";

import React, { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  BarChart3,
  TrendingUp,
  Clock,
  Zap,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ClosedTrade {
  id: string;
  asset: string;
  direction: "LONG" | "SHORT";
  entryPrice: number;
  exitPrice: number;
  size: number;
  pnl: number;
  pnlPercent: number;
  openedAt: string;
  closedAt: string;
}

interface TradeStatsDashboardProps {
  closedTrades: ClosedTrade[];
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmt(n: number, decimals = 2): string {
  return n.toFixed(decimals);
}

function fmtPct(n: number): string {
  return `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`;
}

function fmtUsd(n: number): string {
  return `${n >= 0 ? "+" : ""}$${Math.abs(n).toFixed(2)}`;
}

function holdingMs(trade: ClosedTrade): number {
  return new Date(trade.closedAt).getTime() - new Date(trade.openedAt).getTime();
}

function formatDuration(ms: number): string {
  const hours = ms / (1000 * 60 * 60);
  if (hours < 1) return `${Math.round(hours * 60)}m`;
  if (hours < 24) return `${fmt(hours, 1)}h`;
  return `${fmt(hours / 24, 1)}d`;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function TradeStatsDashboard({ closedTrades }: TradeStatsDashboardProps) {
  // Sort chronologically
  const sorted = useMemo(
    () =>
      [...closedTrades].sort(
        (a, b) =>
          new Date(a.closedAt).getTime() - new Date(b.closedAt).getTime()
      ),
    [closedTrades]
  );

  // =========================================================================
  // 1. Win/Loss Distribution
  // =========================================================================

  const winLoss = useMemo(() => {
    const wins = sorted.filter((t) => t.pnl > 0);
    const losses = sorted.filter((t) => t.pnl <= 0);

    const longTrades = sorted.filter((t) => t.direction === "LONG");
    const shortTrades = sorted.filter((t) => t.direction === "SHORT");

    const longWins = longTrades.filter((t) => t.pnl > 0).length;
    const longLosses = longTrades.length - longWins;
    const shortWins = shortTrades.filter((t) => t.pnl > 0).length;
    const shortLosses = shortTrades.length - shortWins;

    return {
      totalWins: wins.length,
      totalLosses: losses.length,
      total: sorted.length,
      longWins,
      longLosses,
      longTotal: longTrades.length,
      shortWins,
      shortLosses,
      shortTotal: shortTrades.length,
    };
  }, [sorted]);

  // =========================================================================
  // 2. P&L Distribution Histogram
  // =========================================================================

  const histogram = useMemo(() => {
    if (sorted.length === 0) return { bins: [], minPct: 0, maxPct: 0 };

    const pcts = sorted.map((t) => t.pnlPercent);
    const minPct = Math.min(...pcts);
    const maxPct = Math.max(...pcts);
    const range = maxPct - minPct || 1;
    const binSize = range / 10;

    const bins: { lo: number; hi: number; count: number; isPositive: boolean }[] = [];
    for (let i = 0; i < 10; i++) {
      const lo = minPct + i * binSize;
      const hi = lo + binSize;
      const count = pcts.filter(
        (p) => (i === 9 ? p >= lo && p <= hi : p >= lo && p < hi)
      ).length;
      bins.push({ lo, hi, count, isPositive: (lo + hi) / 2 >= 0 });
    }

    return { bins, minPct, maxPct };
  }, [sorted]);

  // =========================================================================
  // 3. Holding Period Analysis
  // =========================================================================

  const holdingAnalysis = useMemo(() => {
    const winners = sorted.filter((t) => t.pnl > 0);
    const losers = sorted.filter((t) => t.pnl <= 0);

    const avgWinHold =
      winners.length > 0
        ? winners.reduce((s, t) => s + holdingMs(t), 0) / winners.length
        : 0;
    const avgLossHold =
      losers.length > 0
        ? losers.reduce((s, t) => s + holdingMs(t), 0) / losers.length
        : 0;

    const ONE_HOUR = 1000 * 60 * 60;
    const ONE_DAY = ONE_HOUR * 24;

    const shortCount = sorted.filter((t) => holdingMs(t) < ONE_HOUR).length;
    const mediumCount = sorted.filter(
      (t) => holdingMs(t) >= ONE_HOUR && holdingMs(t) < ONE_DAY
    ).length;
    const longCount = sorted.filter((t) => holdingMs(t) >= ONE_DAY).length;

    return {
      avgWinHold,
      avgLossHold,
      shortCount,
      mediumCount,
      longCount,
      maxBucket: Math.max(shortCount, mediumCount, longCount, 1),
    };
  }, [sorted]);

  // =========================================================================
  // 4. Streak Analysis
  // =========================================================================

  const streaks = useMemo(() => {
    if (sorted.length === 0)
      return {
        current: { type: "none" as const, count: 0 },
        longestWin: 0,
        longestLoss: 0,
        last20: [] as boolean[],
      };

    let longestWin = 0;
    let longestLoss = 0;
    let cw = 0;
    let cl = 0;

    for (const t of sorted) {
      if (t.pnl > 0) {
        cw++;
        cl = 0;
        longestWin = Math.max(longestWin, cw);
      } else {
        cl++;
        cw = 0;
        longestLoss = Math.max(longestLoss, cl);
      }
    }

    // Current streak is whatever cw or cl is non-zero at the end
    const currentType = cw > 0 ? ("win" as const) : cl > 0 ? ("loss" as const) : ("none" as const);
    const currentCount = cw > 0 ? cw : cl;

    const last20 = sorted
      .slice(-20)
      .map((t) => t.pnl > 0);

    return { current: { type: currentType, count: currentCount }, longestWin, longestLoss, last20 };
  }, [sorted]);

  // =========================================================================
  // 5. Performance by Direction
  // =========================================================================

  const directionStats = useMemo(() => {
    const compute = (trades: ClosedTrade[]) => {
      const count = trades.length;
      if (count === 0)
        return { count: 0, winRate: 0, avgReturn: 0, totalPnl: 0 };

      const wins = trades.filter((t) => t.pnl > 0).length;
      const winRate = (wins / count) * 100;
      const avgReturn =
        trades.reduce((s, t) => s + t.pnlPercent, 0) / count;
      const totalPnl = trades.reduce((s, t) => s + t.pnl, 0);

      return { count, winRate, avgReturn, totalPnl };
    };

    return {
      long: compute(sorted.filter((t) => t.direction === "LONG")),
      short: compute(sorted.filter((t) => t.direction === "SHORT")),
    };
  }, [sorted]);

  // =========================================================================
  // SVG: P&L Distribution Histogram
  // =========================================================================

  const histogramSvg = useMemo(() => {
    const { bins } = histogram;
    if (bins.length === 0) return null;

    const W = 600;
    const H = 180;
    const padL = 35;
    const padR = 10;
    const padT = 10;
    const padB = 40;
    const chartW = W - padL - padR;
    const chartH = H - padT - padB;

    const maxCount = Math.max(...bins.map((b) => b.count), 1);
    const barW = chartW / bins.length - 2;

    return (
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ height: 180 }}>
        {/* Y-axis ticks */}
        {[0, Math.ceil(maxCount / 2), maxCount].map((tick, i) => (
          <g key={i}>
            <line
              x1={padL}
              y1={padT + chartH - (tick / maxCount) * chartH}
              x2={W - padR}
              y2={padT + chartH - (tick / maxCount) * chartH}
              stroke="currentColor"
              className="text-border/30"
              strokeWidth="0.5"
              strokeDasharray="4 4"
            />
            <text
              x={padL - 5}
              y={padT + chartH - (tick / maxCount) * chartH + 4}
              textAnchor="end"
              className="fill-muted-foreground"
              fontSize="9"
            >
              {tick}
            </text>
          </g>
        ))}

        {/* Bars */}
        {bins.map((bin, i) => {
          const barH = (bin.count / maxCount) * chartH;
          const x = padL + i * (chartW / bins.length) + 1;
          const y = padT + chartH - barH;

          return (
            <g key={i}>
              <rect
                x={x}
                y={y}
                width={barW}
                height={Math.max(barH, 0)}
                rx="2"
                fill={bin.isPositive ? "#22c55e" : "#ef4444"}
                fillOpacity="0.7"
              />
              {bin.count > 0 && (
                <text
                  x={x + barW / 2}
                  y={y - 3}
                  textAnchor="middle"
                  className="fill-muted-foreground"
                  fontSize="8"
                >
                  {bin.count}
                </text>
              )}
              {/* X-axis label */}
              <text
                x={x + barW / 2}
                y={H - padB + 12}
                textAnchor="middle"
                className="fill-muted-foreground"
                fontSize="7"
                transform={`rotate(-30, ${x + barW / 2}, ${H - padB + 12})`}
              >
                {fmt(bin.lo, 1)}%
              </text>
            </g>
          );
        })}

        {/* Baseline */}
        <line
          x1={padL}
          y1={padT + chartH}
          x2={W - padR}
          y2={padT + chartH}
          stroke="currentColor"
          className="text-border/50"
          strokeWidth="1"
        />
      </svg>
    );
  }, [histogram]);

  // =========================================================================
  // SVG: Holding Period Bar Chart
  // =========================================================================

  const holdingBarSvg = useMemo(() => {
    const { shortCount, mediumCount, longCount, maxBucket } = holdingAnalysis;
    const buckets = [
      { label: "<1h", count: shortCount },
      { label: "1h-24h", count: mediumCount },
      { label: ">24h", count: longCount },
    ];

    const W = 300;
    const H = 120;
    const padL = 50;
    const padR = 30;
    const padT = 10;
    const padB = 25;
    const chartW = W - padL - padR;
    const chartH = H - padT - padB;
    const barH = Math.min(20, (chartH - 12) / 3);
    const gap = (chartH - barH * 3) / 2;

    return (
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ height: 120 }}>
        {buckets.map((b, i) => {
          const y = padT + i * (barH + gap);
          const barWidth = (b.count / maxBucket) * chartW;

          return (
            <g key={b.label}>
              <text
                x={padL - 5}
                y={y + barH / 2 + 4}
                textAnchor="end"
                className="fill-muted-foreground"
                fontSize="10"
              >
                {b.label}
              </text>
              <rect
                x={padL}
                y={y + 2}
                width={Math.max(barWidth, 2)}
                height={barH - 4}
                rx="3"
                fill="#3b82f6"
                fillOpacity="0.7"
              />
              <text
                x={padL + barWidth + 5}
                y={y + barH / 2 + 4}
                textAnchor="start"
                className="fill-muted-foreground"
                fontSize="10"
                fontFamily="monospace"
              >
                {b.count}
              </text>
            </g>
          );
        })}
      </svg>
    );
  }, [holdingAnalysis]);

  // =========================================================================
  // Guard
  // =========================================================================

  if (closedTrades.length < 2) return null;

  // =========================================================================
  // Render
  // =========================================================================

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2">
        <BarChart3 className="h-5 w-5 text-muted-foreground" />
        <h2 className="text-sm font-medium text-muted-foreground">
          Trade Statistics
        </h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* ================================================================ */}
        {/* 1. Win/Loss Distribution */}
        {/* ================================================================ */}
        <Card className="border-border/50 bg-card/50">
          <CardHeader className="pb-3 pt-4 px-4">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-green-400" />
              Win/Loss Distribution
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4 pt-0 space-y-3">
            {/* Overall bar */}
            <div>
              <div className="flex justify-between text-xs text-muted-foreground mb-1">
                <span>Overall</span>
                <span className="font-mono">
                  {winLoss.totalWins} wins / {winLoss.totalLosses} losses
                </span>
              </div>
              <div className="h-3 rounded-full overflow-hidden flex bg-muted/30">
                {winLoss.total > 0 && (
                  <>
                    <div
                      className="bg-green-500/70 h-full transition-all"
                      style={{
                        width: `${(winLoss.totalWins / winLoss.total) * 100}%`,
                      }}
                    />
                    <div
                      className="bg-red-500/70 h-full transition-all"
                      style={{
                        width: `${(winLoss.totalLosses / winLoss.total) * 100}%`,
                      }}
                    />
                  </>
                )}
              </div>
            </div>

            {/* Long bar */}
            {winLoss.longTotal > 0 && (
              <div>
                <div className="flex justify-between text-xs text-muted-foreground mb-1">
                  <span className="flex items-center gap-1">
                    <ArrowUpRight className="h-3 w-3 text-green-400" />
                    LONG
                  </span>
                  <span className="font-mono">
                    {winLoss.longWins}W / {winLoss.longLosses}L
                  </span>
                </div>
                <div className="h-2.5 rounded-full overflow-hidden flex bg-muted/30">
                  <div
                    className="bg-green-500/60 h-full"
                    style={{
                      width: `${(winLoss.longWins / winLoss.longTotal) * 100}%`,
                    }}
                  />
                  <div
                    className="bg-red-500/60 h-full"
                    style={{
                      width: `${(winLoss.longLosses / winLoss.longTotal) * 100}%`,
                    }}
                  />
                </div>
              </div>
            )}

            {/* Short bar */}
            {winLoss.shortTotal > 0 && (
              <div>
                <div className="flex justify-between text-xs text-muted-foreground mb-1">
                  <span className="flex items-center gap-1">
                    <ArrowDownRight className="h-3 w-3 text-red-400" />
                    SHORT
                  </span>
                  <span className="font-mono">
                    {winLoss.shortWins}W / {winLoss.shortLosses}L
                  </span>
                </div>
                <div className="h-2.5 rounded-full overflow-hidden flex bg-muted/30">
                  <div
                    className="bg-green-500/60 h-full"
                    style={{
                      width: `${(winLoss.shortWins / winLoss.shortTotal) * 100}%`,
                    }}
                  />
                  <div
                    className="bg-red-500/60 h-full"
                    style={{
                      width: `${(winLoss.shortLosses / winLoss.shortTotal) * 100}%`,
                    }}
                  />
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* ================================================================ */}
        {/* 4. Streak Analysis */}
        {/* ================================================================ */}
        <Card className="border-border/50 bg-card/50">
          <CardHeader className="pb-3 pt-4 px-4">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Zap className="h-4 w-4 text-yellow-400" />
              Streak Analysis
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4 pt-0 space-y-3">
            {/* Current Streak */}
            <div className="flex items-center gap-3">
              <span className="text-xs text-muted-foreground w-24">
                Current Streak
              </span>
              <Badge
                variant={
                  streaks.current.type === "win"
                    ? "default"
                    : streaks.current.type === "loss"
                    ? "destructive"
                    : "secondary"
                }
                className={cn(
                  "font-mono text-xs",
                  streaks.current.type === "win" &&
                    "bg-green-500/20 text-green-400 border-green-500/30"
                )}
              >
                {streaks.current.type === "none"
                  ? "N/A"
                  : `${streaks.current.count} ${streaks.current.type === "win" ? "Win" : "Loss"}${
                      streaks.current.count !== 1 ? "s" : ""
                    }`}
              </Badge>
            </div>

            {/* Longest streaks */}
            <div className="grid grid-cols-2 gap-2">
              <div className="rounded-lg border border-border/40 bg-card/30 p-2.5">
                <div className="text-[10px] text-muted-foreground mb-0.5">
                  Longest Win Streak
                </div>
                <div className="text-lg font-bold font-mono text-green-400">
                  {streaks.longestWin}
                </div>
              </div>
              <div className="rounded-lg border border-border/40 bg-card/30 p-2.5">
                <div className="text-[10px] text-muted-foreground mb-0.5">
                  Longest Loss Streak
                </div>
                <div className="text-lg font-bold font-mono text-red-400">
                  {streaks.longestLoss}
                </div>
              </div>
            </div>

            {/* Streak Timeline (last 20 trades) */}
            {streaks.last20.length > 0 && (
              <div>
                <div className="text-[10px] text-muted-foreground mb-1.5">
                  Last {streaks.last20.length} Trades
                </div>
                <div className="flex items-center gap-1 flex-wrap">
                  {streaks.last20.map((isWin, i) => (
                    <div
                      key={i}
                      className={cn(
                        "h-3 w-3 rounded-full transition-colors",
                        isWin ? "bg-green-500" : "bg-red-500"
                      )}
                      title={`Trade ${i + 1}: ${isWin ? "Win" : "Loss"}`}
                    />
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* ================================================================ */}
        {/* 2. P&L Distribution Histogram */}
        {/* ================================================================ */}
        <Card className="border-border/50 bg-card/50">
          <CardHeader className="pb-3 pt-4 px-4">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-blue-400" />
              P&L Distribution
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4 pt-0">
            {histogramSvg}
          </CardContent>
        </Card>

        {/* ================================================================ */}
        {/* 3. Holding Period Analysis */}
        {/* ================================================================ */}
        <Card className="border-border/50 bg-card/50">
          <CardHeader className="pb-3 pt-4 px-4">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Clock className="h-4 w-4 text-purple-400" />
              Holding Period Analysis
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4 pt-0 space-y-3">
            {/* Avg holding for winners vs losers */}
            <div className="grid grid-cols-2 gap-2">
              <div className="rounded-lg border border-border/40 bg-card/30 p-2.5">
                <div className="text-[10px] text-muted-foreground mb-0.5">
                  Avg Hold (Winners)
                </div>
                <div className="text-base font-bold font-mono text-green-400">
                  {formatDuration(holdingAnalysis.avgWinHold)}
                </div>
              </div>
              <div className="rounded-lg border border-border/40 bg-card/30 p-2.5">
                <div className="text-[10px] text-muted-foreground mb-0.5">
                  Avg Hold (Losers)
                </div>
                <div className="text-base font-bold font-mono text-red-400">
                  {formatDuration(holdingAnalysis.avgLossHold)}
                </div>
              </div>
            </div>

            {/* Duration bucket chart */}
            {holdingBarSvg}
          </CardContent>
        </Card>
      </div>

      {/* ================================================================== */}
      {/* 5. Performance by Direction */}
      {/* ================================================================== */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* LONG card */}
        <Card className="border-border/50 bg-card/50">
          <CardHeader className="pb-3 pt-4 px-4">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <ArrowUpRight className="h-4 w-4 text-green-400" />
              LONG Performance
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4 pt-0">
            <div className="grid grid-cols-2 gap-2">
              <div className="rounded-lg border border-border/40 bg-card/30 p-2.5">
                <div className="text-[10px] text-muted-foreground mb-0.5">
                  Trades
                </div>
                <div className="text-base font-bold font-mono text-white">
                  {directionStats.long.count}
                </div>
              </div>
              <div className="rounded-lg border border-border/40 bg-card/30 p-2.5">
                <div className="text-[10px] text-muted-foreground mb-0.5">
                  Win Rate
                </div>
                <div
                  className={cn(
                    "text-base font-bold font-mono",
                    directionStats.long.winRate >= 50
                      ? "text-green-400"
                      : "text-red-400"
                  )}
                >
                  {fmt(directionStats.long.winRate, 1)}%
                </div>
              </div>
              <div className="rounded-lg border border-border/40 bg-card/30 p-2.5">
                <div className="text-[10px] text-muted-foreground mb-0.5">
                  Avg Return
                </div>
                <div
                  className={cn(
                    "text-base font-bold font-mono",
                    directionStats.long.avgReturn >= 0
                      ? "text-green-400"
                      : "text-red-400"
                  )}
                >
                  {fmtPct(directionStats.long.avgReturn)}
                </div>
              </div>
              <div className="rounded-lg border border-border/40 bg-card/30 p-2.5">
                <div className="text-[10px] text-muted-foreground mb-0.5">
                  Total P&L
                </div>
                <div
                  className={cn(
                    "text-base font-bold font-mono",
                    directionStats.long.totalPnl >= 0
                      ? "text-green-400"
                      : "text-red-400"
                  )}
                >
                  {fmtUsd(directionStats.long.totalPnl)}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* SHORT card */}
        <Card className="border-border/50 bg-card/50">
          <CardHeader className="pb-3 pt-4 px-4">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <ArrowDownRight className="h-4 w-4 text-red-400" />
              SHORT Performance
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4 pt-0">
            <div className="grid grid-cols-2 gap-2">
              <div className="rounded-lg border border-border/40 bg-card/30 p-2.5">
                <div className="text-[10px] text-muted-foreground mb-0.5">
                  Trades
                </div>
                <div className="text-base font-bold font-mono text-white">
                  {directionStats.short.count}
                </div>
              </div>
              <div className="rounded-lg border border-border/40 bg-card/30 p-2.5">
                <div className="text-[10px] text-muted-foreground mb-0.5">
                  Win Rate
                </div>
                <div
                  className={cn(
                    "text-base font-bold font-mono",
                    directionStats.short.winRate >= 50
                      ? "text-green-400"
                      : "text-red-400"
                  )}
                >
                  {fmt(directionStats.short.winRate, 1)}%
                </div>
              </div>
              <div className="rounded-lg border border-border/40 bg-card/30 p-2.5">
                <div className="text-[10px] text-muted-foreground mb-0.5">
                  Avg Return
                </div>
                <div
                  className={cn(
                    "text-base font-bold font-mono",
                    directionStats.short.avgReturn >= 0
                      ? "text-green-400"
                      : "text-red-400"
                  )}
                >
                  {fmtPct(directionStats.short.avgReturn)}
                </div>
              </div>
              <div className="rounded-lg border border-border/40 bg-card/30 p-2.5">
                <div className="text-[10px] text-muted-foreground mb-0.5">
                  Total P&L
                </div>
                <div
                  className={cn(
                    "text-base font-bold font-mono",
                    directionStats.short.totalPnl >= 0
                      ? "text-green-400"
                      : "text-red-400"
                  )}
                >
                  {fmtUsd(directionStats.short.totalPnl)}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
