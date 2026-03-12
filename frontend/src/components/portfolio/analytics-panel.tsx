// =============================================================================
// src/components/portfolio/analytics-panel.tsx — Advanced Portfolio Analytics
// =============================================================================

"use client";

import React, { useMemo } from "react";
import type { ClosedTrade } from "@/lib/types";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface AnalyticsPanelProps {
  closedTrades: ClosedTrade[];
  totalCapital: number;
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

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

// ---------------------------------------------------------------------------
// Stat Card (local)
// ---------------------------------------------------------------------------

function StatCard({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-border/50 bg-card/50 p-4">
      <div className="text-xs text-muted-foreground mb-1">{label}</div>
      <div className="text-lg font-bold font-mono text-white">{children}</div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function AnalyticsPanel({
  closedTrades,
  totalCapital,
}: AnalyticsPanelProps) {
  // Sort trades chronologically (oldest first) for equity curve
  const sorted = useMemo(
    () =>
      [...closedTrades].sort(
        (a, b) => new Date(a.closedAt).getTime() - new Date(b.closedAt).getTime()
      ),
    [closedTrades]
  );

  // =========================================================================
  // 1. Advanced Performance Metrics
  // =========================================================================

  const metrics = useMemo(() => {
    const returns = sorted.map((t) => t.pnlPercent / 100);
    const n = returns.length;
    if (n === 0)
      return {
        sharpe: 0,
        profitFactor: 0,
        avgHoldingHrs: 0,
        bestTrade: 0,
        worstTrade: 0,
        maxConsecWins: 0,
        maxConsecLosses: 0,
      };

    // Sharpe Ratio
    const riskFreeDaily = 0.04 / 365;
    const avgReturn = returns.reduce((s, r) => s + r, 0) / n;
    const variance =
      returns.reduce((s, r) => s + (r - avgReturn) ** 2, 0) / Math.max(n - 1, 1);
    const stdDev = Math.sqrt(variance);
    const sharpe = stdDev > 0 ? (avgReturn - riskFreeDaily) / stdDev : 0;

    // Profit Factor
    const totalWins = sorted
      .filter((t) => t.pnl > 0)
      .reduce((s, t) => s + t.pnl, 0);
    const totalLosses = Math.abs(
      sorted.filter((t) => t.pnl < 0).reduce((s, t) => s + t.pnl, 0)
    );
    const profitFactor = totalLosses > 0 ? totalWins / totalLosses : totalWins > 0 ? Infinity : 0;

    // Avg Holding Period
    const holdingMs = sorted.map(
      (t) => new Date(t.closedAt).getTime() - new Date(t.openedAt).getTime()
    );
    const avgHoldingHrs =
      holdingMs.reduce((s, ms) => s + ms, 0) / n / (1000 * 60 * 60);

    // Best / Worst Trade
    const pnls = sorted.map((t) => t.pnl);
    const bestTrade = Math.max(...pnls);
    const worstTrade = Math.min(...pnls);

    // Consecutive Wins / Losses
    let maxConsecWins = 0;
    let maxConsecLosses = 0;
    let cw = 0;
    let cl = 0;
    for (const t of sorted) {
      if (t.pnl > 0) {
        cw++;
        cl = 0;
        maxConsecWins = Math.max(maxConsecWins, cw);
      } else {
        cl++;
        cw = 0;
        maxConsecLosses = Math.max(maxConsecLosses, cl);
      }
    }

    return {
      sharpe,
      profitFactor,
      avgHoldingHrs,
      bestTrade,
      worstTrade,
      maxConsecWins,
      maxConsecLosses,
    };
  }, [sorted]);

  // =========================================================================
  // 2. Monthly Returns Heatmap
  // =========================================================================

  const monthlyData = useMemo(() => {
    const byMonth: Record<string, number> = {};
    const capitalByMonth: Record<string, number> = {};

    for (const t of sorted) {
      const d = new Date(t.closedAt);
      const key = `${d.getFullYear()}-${String(d.getMonth()).padStart(2, "0")}`;
      byMonth[key] = (byMonth[key] || 0) + t.pnl;
      capitalByMonth[key] = totalCapital; // simplified: use totalCapital as base
    }

    // Compute return % per month
    const returnByMonth: Record<string, number> = {};
    for (const key of Object.keys(byMonth)) {
      returnByMonth[key] = (byMonth[key] / totalCapital) * 100;
    }

    // Get year range
    const years = Array.from(
      new Set(Object.keys(returnByMonth).map((k) => parseInt(k.split("-")[0])))
    ).sort();

    return { returnByMonth, years };
  }, [sorted, totalCapital]);

  // =========================================================================
  // 3. Drawdown Chart
  // =========================================================================

  const drawdownData = useMemo(() => {
    if (sorted.length === 0) return [];

    let equity = totalCapital;
    let peak = equity;
    const points: { index: number; date: string; drawdown: number; equity: number }[] = [];

    points.push({ index: 0, date: "", drawdown: 0, equity });

    for (let i = 0; i < sorted.length; i++) {
      equity += sorted[i].pnl;
      peak = Math.max(peak, equity);
      const dd = peak > 0 ? ((peak - equity) / peak) * 100 : 0;
      points.push({
        index: i + 1,
        date: sorted[i].closedAt,
        drawdown: dd,
        equity,
      });
    }

    return points;
  }, [sorted, totalCapital]);

  // =========================================================================
  // 4. Performance by Day of Week
  // =========================================================================

  const dayOfWeekData = useMemo(() => {
    const buckets: Record<number, { totalReturn: number; count: number }> = {};
    for (let i = 0; i < 7; i++) buckets[i] = { totalReturn: 0, count: 0 };

    for (const t of sorted) {
      const day = new Date(t.closedAt).getDay();
      buckets[day].totalReturn += t.pnlPercent;
      buckets[day].count++;
    }

    // Return Mon-Sun order (1,2,3,4,5,6,0)
    const order = [1, 2, 3, 4, 5, 6, 0];
    return order.map((d) => ({
      day: DAYS[d],
      avgReturn: buckets[d].count > 0 ? buckets[d].totalReturn / buckets[d].count : 0,
      count: buckets[d].count,
    }));
  }, [sorted]);

  // =========================================================================
  // Drawdown SVG
  // =========================================================================

  const drawdownSvg = useMemo(() => {
    if (drawdownData.length < 2) return null;

    const W = 800;
    const H = 160;
    const padL = 45;
    const padR = 10;
    const padT = 10;
    const padB = 25;
    const chartW = W - padL - padR;
    const chartH = H - padT - padB;

    const maxDD = Math.max(...drawdownData.map((d) => d.drawdown), 1);
    const n = drawdownData.length;

    const xScale = (i: number) => padL + (i / (n - 1)) * chartW;
    const yScale = (dd: number) => padT + (dd / maxDD) * chartH;

    // Build area path
    let areaPath = `M ${xScale(0)} ${yScale(0)}`;
    for (let i = 1; i < n; i++) {
      areaPath += ` L ${xScale(i)} ${yScale(drawdownData[i].drawdown)}`;
    }
    areaPath += ` L ${xScale(n - 1)} ${yScale(0)} Z`;

    // Build line path
    let linePath = `M ${xScale(0)} ${yScale(0)}`;
    for (let i = 1; i < n; i++) {
      linePath += ` L ${xScale(i)} ${yScale(drawdownData[i].drawdown)}`;
    }

    // Y-axis labels
    const yTicks = [0, maxDD / 2, maxDD];

    return (
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="w-full"
        style={{ height: 160 }}
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id="dd-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ef4444" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#ef4444" stopOpacity="0.05" />
          </linearGradient>
        </defs>

        {/* Grid lines */}
        {yTicks.map((tick, i) => (
          <g key={i}>
            <line
              x1={padL}
              y1={yScale(tick)}
              x2={W - padR}
              y2={yScale(tick)}
              stroke="currentColor"
              className="text-border/30"
              strokeWidth="0.5"
              strokeDasharray={tick > 0 ? "4 4" : undefined}
            />
            <text
              x={padL - 5}
              y={yScale(tick) + 4}
              textAnchor="end"
              className="fill-muted-foreground"
              fontSize="10"
            >
              -{fmt(tick, 1)}%
            </text>
          </g>
        ))}

        {/* Area fill */}
        <path d={areaPath} fill="url(#dd-grad)" />

        {/* Line */}
        <path
          d={linePath}
          fill="none"
          stroke="#ef4444"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />

        {/* X-axis labels */}
        {n > 1 && (
          <>
            <text
              x={xScale(0)}
              y={H - 5}
              textAnchor="start"
              className="fill-muted-foreground"
              fontSize="9"
            >
              #1
            </text>
            <text
              x={xScale(n - 1)}
              y={H - 5}
              textAnchor="end"
              className="fill-muted-foreground"
              fontSize="9"
            >
              #{n}
            </text>
            {n > 4 && (
              <text
                x={xScale(Math.floor(n / 2))}
                y={H - 5}
                textAnchor="middle"
                className="fill-muted-foreground"
                fontSize="9"
              >
                #{Math.floor(n / 2) + 1}
              </text>
            )}
          </>
        )}

        {/* Baseline */}
        <line
          x1={padL}
          y1={yScale(0)}
          x2={W - padR}
          y2={yScale(0)}
          stroke="currentColor"
          className="text-border/50"
          strokeWidth="1"
        />
      </svg>
    );
  }, [drawdownData]);

  // =========================================================================
  // Day-of-week bar chart SVG
  // =========================================================================

  const dayBarSvg = useMemo(() => {
    const data = dayOfWeekData;
    const maxAbs = Math.max(...data.map((d) => Math.abs(d.avgReturn)), 0.1);

    const W = 500;
    const H = 200;
    const padL = 40;
    const padR = 60;
    const barH = 20;
    const gap = 6;
    const centerX = padL + (W - padL - padR) / 2;
    const halfW = (W - padL - padR) / 2;

    return (
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ height: 200 }}>
        {data.map((d, i) => {
          const y = 10 + i * (barH + gap);
          const barWidth = (Math.abs(d.avgReturn) / maxAbs) * halfW;
          const isPositive = d.avgReturn >= 0;
          const barX = isPositive ? centerX : centerX - barWidth;

          return (
            <g key={d.day}>
              {/* Day label */}
              <text
                x={padL - 5}
                y={y + barH / 2 + 4}
                textAnchor="end"
                className="fill-muted-foreground"
                fontSize="11"
              >
                {d.day}
              </text>

              {/* Center line */}
              <line
                x1={centerX}
                y1={y}
                x2={centerX}
                y2={y + barH}
                stroke="currentColor"
                className="text-border/30"
                strokeWidth="0.5"
              />

              {/* Bar */}
              {d.count > 0 && (
                <rect
                  x={barX}
                  y={y + 2}
                  width={Math.max(barWidth, 1)}
                  height={barH - 4}
                  rx="3"
                  fill={isPositive ? "#22c55e" : "#ef4444"}
                  fillOpacity="0.7"
                />
              )}

              {/* Value label */}
              <text
                x={W - padR + 5}
                y={y + barH / 2 + 4}
                textAnchor="start"
                className="fill-muted-foreground"
                fontSize="10"
                fontFamily="monospace"
              >
                {d.count > 0 ? `${fmtPct(d.avgReturn)} (${d.count})` : "-- (0)"}
              </text>
            </g>
          );
        })}

        {/* Center baseline */}
        <line
          x1={centerX}
          y1={5}
          x2={centerX}
          y2={10 + data.length * (barH + gap)}
          stroke="currentColor"
          className="text-border/50"
          strokeWidth="1"
        />
      </svg>
    );
  }, [dayOfWeekData]);

  // =========================================================================
  // Monthly heatmap color
  // =========================================================================

  function heatColor(val: number | undefined): string {
    if (val === undefined) return "bg-muted/20 text-muted-foreground/50";
    if (val === 0) return "bg-muted/30 text-muted-foreground";
    if (val > 0) {
      if (val > 5) return "bg-green-500/60 text-white";
      if (val > 2) return "bg-green-500/40 text-green-100";
      return "bg-green-500/20 text-green-300";
    }
    if (val < -5) return "bg-red-500/60 text-white";
    if (val < -2) return "bg-red-500/40 text-red-100";
    return "bg-red-500/20 text-red-300";
  }

  // =========================================================================
  // Render
  // =========================================================================

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div className="flex items-center gap-2">
        <svg
          className="h-5 w-5 text-muted-foreground"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
          />
        </svg>
        <h2 className="text-sm font-medium text-muted-foreground">
          Portfolio Analytics
        </h2>
      </div>

      {/* 1. Advanced Performance Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        <StatCard label="Sharpe Ratio">
          <span
            className={
              metrics.sharpe > 1
                ? "text-green-400"
                : metrics.sharpe > 0
                ? "text-yellow-400"
                : "text-red-400"
            }
          >
            {fmt(metrics.sharpe)}
          </span>
        </StatCard>

        <StatCard label="Profit Factor">
          <span
            className={
              metrics.profitFactor > 1.5
                ? "text-green-400"
                : metrics.profitFactor >= 1
                ? "text-yellow-400"
                : "text-red-400"
            }
          >
            {metrics.profitFactor === Infinity ? "INF" : fmt(metrics.profitFactor)}
          </span>
        </StatCard>

        <StatCard label="Avg Holding">
          <span className="text-white">
            {metrics.avgHoldingHrs < 1
              ? `${fmt(metrics.avgHoldingHrs * 60, 0)}m`
              : metrics.avgHoldingHrs < 24
              ? `${fmt(metrics.avgHoldingHrs, 1)}h`
              : `${fmt(metrics.avgHoldingHrs / 24, 1)}d`}
          </span>
        </StatCard>

        <StatCard label="Best Trade">
          <span className="text-green-400">{fmtUsd(metrics.bestTrade)}</span>
        </StatCard>

        <StatCard label="Worst Trade">
          <span className="text-red-400">{fmtUsd(metrics.worstTrade)}</span>
        </StatCard>

        <StatCard label="Consec. Wins">
          <span className="text-green-400">{metrics.maxConsecWins}</span>
        </StatCard>

        <StatCard label="Consec. Losses">
          <span className="text-red-400">{metrics.maxConsecLosses}</span>
        </StatCard>
      </div>

      {/* 2. Monthly Returns Heatmap */}
      {monthlyData.years.length > 0 && (
        <div className="rounded-xl border border-border/50 bg-card/50 p-4">
          <div className="text-xs text-muted-foreground mb-3 font-medium">
            Monthly Returns Heatmap
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-center">
              <thead>
                <tr>
                  <th className="text-[10px] text-muted-foreground font-normal pb-2 pr-2 text-left">
                    Year
                  </th>
                  {MONTHS.map((m) => (
                    <th
                      key={m}
                      className="text-[10px] text-muted-foreground font-normal pb-2 px-0.5"
                    >
                      {m}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {monthlyData.years.map((year) => (
                  <tr key={year}>
                    <td className="text-xs text-muted-foreground font-mono pr-2 py-0.5 text-left">
                      {year}
                    </td>
                    {Array.from({ length: 12 }, (_, m) => {
                      const key = `${year}-${String(m).padStart(2, "0")}`;
                      const val = monthlyData.returnByMonth[key];
                      return (
                        <td key={m} className="px-0.5 py-0.5">
                          <div
                            className={`rounded px-1 py-1.5 text-[10px] font-mono ${heatColor(val)}`}
                          >
                            {val !== undefined ? fmtPct(val) : "--"}
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 3. Drawdown Chart */}
      {drawdownData.length >= 2 && (
        <div className="rounded-xl border border-border/50 bg-card/50 p-4">
          <div className="text-xs text-muted-foreground mb-3 font-medium">
            Drawdown Over Trades
          </div>
          {drawdownSvg}
        </div>
      )}

      {/* 4. Performance by Day of Week */}
      <div className="rounded-xl border border-border/50 bg-card/50 p-4">
        <div className="text-xs text-muted-foreground mb-3 font-medium">
          Avg Return by Day of Week
        </div>
        {dayBarSvg}
      </div>
    </div>
  );
}
