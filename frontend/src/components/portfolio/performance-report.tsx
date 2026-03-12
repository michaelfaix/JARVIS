"use client";

import React, { useMemo } from "react";
import type { ClosedTrade } from "@/lib/types";

interface PerformanceReportProps {
  closedTrades: ClosedTrade[];
  totalCapital: number;
  totalValue: number;
  winRate: number;
}

function formatCurrency(v: number, decimals = 2): string {
  return v.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function PerformanceReport({
  closedTrades,
  totalCapital,
  totalValue,
  winRate,
}: PerformanceReportProps) {
  // Period calculation
  const period = useMemo(() => {
    if (closedTrades.length === 0) return { from: "—", to: "—" };
    const sorted = [...closedTrades].sort(
      (a, b) => new Date(a.closedAt).getTime() - new Date(b.closedAt).getTime()
    );
    const fmt = (d: string) =>
      new Date(d).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    return { from: fmt(sorted[0].closedAt), to: fmt(sorted[sorted.length - 1].closedAt) };
  }, [closedTrades]);

  // Total return
  const totalReturn = totalCapital > 0 ? ((totalValue - totalCapital) / totalCapital) * 100 : 0;
  const totalReturnDollar = totalValue - totalCapital;
  const isProfit = totalReturnDollar >= 0;

  // Profit factor
  const profitFactor = useMemo(() => {
    const grossWin = closedTrades
      .filter((t) => t.pnl > 0)
      .reduce((s, t) => s + t.pnl, 0);
    const grossLoss = Math.abs(
      closedTrades.filter((t) => t.pnl < 0).reduce((s, t) => s + t.pnl, 0)
    );
    return grossLoss > 0 ? grossWin / grossLoss : grossWin > 0 ? Infinity : 0;
  }, [closedTrades]);

  // Equity curve data points
  const equityPoints = useMemo(() => {
    if (closedTrades.length === 0) return [];
    const sorted = [...closedTrades].sort(
      (a, b) => new Date(a.closedAt).getTime() - new Date(b.closedAt).getTime()
    );
    let equity = totalCapital;
    const points: number[] = [equity];
    for (const t of sorted) {
      equity += t.pnl;
      points.push(equity);
    }
    return points;
  }, [closedTrades, totalCapital]);

  // Top / worst performers
  const { best, worst } = useMemo(() => {
    const sorted = [...closedTrades].sort((a, b) => b.pnlPercent - a.pnlPercent);
    return {
      best: sorted.slice(0, 3),
      worst: sorted.slice(-3).reverse(),
    };
  }, [closedTrades]);

  // Monthly breakdown
  const monthly = useMemo(() => {
    if (closedTrades.length === 0) return [];
    const map = new Map<
      string,
      { month: string; trades: number; pnl: number; wins: number }
    >();
    for (const t of closedTrades) {
      const d = new Date(t.closedAt);
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
      const label = d.toLocaleDateString("en-US", { month: "short", year: "numeric" });
      if (!map.has(key)) map.set(key, { month: label, trades: 0, pnl: 0, wins: 0 });
      const entry = map.get(key)!;
      entry.trades++;
      entry.pnl += t.pnl;
      if (t.pnl > 0) entry.wins++;
    }
    return Array.from(map.entries())
      .sort((a, b) => b[0].localeCompare(a[0]))
      .slice(0, 6)
      .map(([, v]) => ({
        ...v,
        winRate: v.trades > 0 ? (v.wins / v.trades) * 100 : 0,
      }));
  }, [closedTrades]);

  // SVG equity mini-chart
  const equitySvg = useMemo(() => {
    if (equityPoints.length < 2) return null;
    const w = 360;
    const h = 80;
    const pad = 4;
    const min = Math.min(...equityPoints);
    const max = Math.max(...equityPoints);
    const range = max - min || 1;
    const points = equityPoints
      .map((v, i) => {
        const x = pad + (i / (equityPoints.length - 1)) * (w - pad * 2);
        const y = h - pad - ((v - min) / range) * (h - pad * 2);
        return `${x},${y}`;
      })
      .join(" ");

    const color = isProfit ? "#4ade80" : "#f87171";
    const gradId = "eq-grad";

    // Area fill points
    const firstX = pad;
    const lastX = pad + ((equityPoints.length - 1) / (equityPoints.length - 1)) * (w - pad * 2);
    const areaPoints = `${firstX},${h - pad} ${points} ${lastX},${h - pad}`;

    return (
      <svg
        viewBox={`0 0 ${w} ${h}`}
        className="w-full"
        style={{ height: 80 }}
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.3" />
            <stop offset="100%" stopColor={color} stopOpacity="0.02" />
          </linearGradient>
        </defs>
        <polygon points={areaPoints} fill={`url(#${gradId})`} />
        <polyline
          points={points}
          fill="none"
          stroke={color}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  }, [equityPoints, isProfit]);

  const generatedAt = new Date().toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div
      id="performance-report"
      className="max-w-md mx-auto bg-card border border-border/50 rounded-xl p-6 space-y-5"
    >
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
            J
          </div>
          <span className="text-sm font-semibold text-white tracking-tight">
            JARVIS Trader — Performance Report
          </span>
        </div>
        <div className="text-[10px] text-muted-foreground flex items-center gap-3 mt-1">
          <span>
            {period.from} — {period.to}
          </span>
          <span className="opacity-50">|</span>
          <span>Generated {generatedAt}</span>
        </div>
      </div>

      {/* Divider */}
      <div className="h-px bg-border/40" />

      {/* Summary Row */}
      <div className="grid grid-cols-4 gap-3">
        <div>
          <div className="text-[10px] text-muted-foreground mb-0.5">Total Return</div>
          <div
            className={`text-sm font-bold font-mono ${isProfit ? "text-green-400" : "text-red-400"}`}
          >
            {isProfit ? "+" : ""}
            {totalReturn.toFixed(2)}%
          </div>
          <div
            className={`text-[10px] font-mono ${isProfit ? "text-green-400/70" : "text-red-400/70"}`}
          >
            {isProfit ? "+" : ""}${formatCurrency(Math.abs(totalReturnDollar), 0)}
          </div>
        </div>
        <div>
          <div className="text-[10px] text-muted-foreground mb-0.5">Win Rate</div>
          <div
            className={`text-sm font-bold font-mono ${winRate >= 50 ? "text-green-400" : "text-red-400"}`}
          >
            {winRate.toFixed(1)}%
          </div>
        </div>
        <div>
          <div className="text-[10px] text-muted-foreground mb-0.5">Total Trades</div>
          <div className="text-sm font-bold font-mono text-white">{closedTrades.length}</div>
        </div>
        <div>
          <div className="text-[10px] text-muted-foreground mb-0.5">Profit Factor</div>
          <div
            className={`text-sm font-bold font-mono ${
              profitFactor >= 1 ? "text-green-400" : "text-red-400"
            }`}
          >
            {profitFactor === Infinity ? "∞" : profitFactor.toFixed(2)}
          </div>
        </div>
      </div>

      {/* Equity Mini-Chart */}
      {equitySvg && (
        <div>
          <div className="text-[10px] text-muted-foreground mb-1">Equity Curve</div>
          <div className="rounded-lg bg-background/40 border border-border/30 overflow-hidden">
            {equitySvg}
          </div>
        </div>
      )}

      {/* Top Performers */}
      {closedTrades.length > 0 && (
        <div className="grid grid-cols-2 gap-4">
          {/* Best trades */}
          <div>
            <div className="text-[10px] text-muted-foreground mb-1.5">Best Trades</div>
            <div className="space-y-1">
              {best.map((t) => (
                <div
                  key={t.id}
                  className="flex items-center justify-between text-[11px]"
                >
                  <span className="text-white font-medium truncate mr-2">
                    {t.asset}{" "}
                    <span className="text-muted-foreground text-[9px]">{t.direction}</span>
                  </span>
                  <span className="text-green-400 font-mono shrink-0">
                    +{t.pnlPercent.toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
          {/* Worst trades */}
          <div>
            <div className="text-[10px] text-muted-foreground mb-1.5">Worst Trades</div>
            <div className="space-y-1">
              {worst.map((t) => (
                <div
                  key={t.id}
                  className="flex items-center justify-between text-[11px]"
                >
                  <span className="text-white font-medium truncate mr-2">
                    {t.asset}{" "}
                    <span className="text-muted-foreground text-[9px]">{t.direction}</span>
                  </span>
                  <span className="text-red-400 font-mono shrink-0">
                    {t.pnlPercent.toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Monthly Breakdown */}
      {monthly.length > 0 && (
        <div>
          <div className="text-[10px] text-muted-foreground mb-1.5">Monthly Breakdown</div>
          <div className="rounded-lg bg-background/40 border border-border/30 overflow-hidden">
            <table className="w-full text-[11px]">
              <thead>
                <tr className="text-muted-foreground border-b border-border/30">
                  <th className="text-left py-1.5 px-2 font-medium">Month</th>
                  <th className="text-right py-1.5 px-2 font-medium">Trades</th>
                  <th className="text-right py-1.5 px-2 font-medium">P&L</th>
                  <th className="text-right py-1.5 px-2 font-medium">Win %</th>
                </tr>
              </thead>
              <tbody>
                {monthly.map((m) => (
                  <tr key={m.month} className="border-b border-border/20 last:border-0">
                    <td className="py-1.5 px-2 text-white">{m.month}</td>
                    <td className="py-1.5 px-2 text-right font-mono text-muted-foreground">
                      {m.trades}
                    </td>
                    <td
                      className={`py-1.5 px-2 text-right font-mono ${
                        m.pnl >= 0 ? "text-green-400" : "text-red-400"
                      }`}
                    >
                      {m.pnl >= 0 ? "+" : ""}${formatCurrency(Math.abs(m.pnl), 0)}
                    </td>
                    <td
                      className={`py-1.5 px-2 text-right font-mono ${
                        m.winRate >= 50 ? "text-green-400" : "text-red-400"
                      }`}
                    >
                      {m.winRate.toFixed(0)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="h-px bg-border/40" />
      <div className="flex items-center justify-between text-[10px] text-muted-foreground/60">
        <span>Generated by JARVIS Trader</span>
        <span>jarvis-trader.app</span>
      </div>
    </div>
  );
}
