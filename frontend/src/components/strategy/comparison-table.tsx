"use client";

import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Trophy,
  Crown,
  TrendingUp,
  TrendingDown,
  BarChart3,
} from "lucide-react";
import { cn } from "@/lib/utils";

export interface BacktestResultSummary {
  strategy: string;
  asset: string;
  period: number; // days
  totalReturn: number; // percentage
  winRate: number; // percentage
  sharpeRatio: number;
  maxDrawdown: number; // percentage
  profitFactor: number;
  totalTrades: number;
  avgWin: number; // percentage
  avgLoss: number; // percentage
}

interface ComparisonTableProps {
  results: BacktestResultSummary[];
}

interface MetricRow {
  label: string;
  key: string;
  getValue: (r: BacktestResultSummary) => number;
  format: (v: number) => string;
  colorFn: (v: number) => string;
  higherIsBetter: boolean;
}

const metrics: MetricRow[] = [
  {
    label: "Total Return",
    key: "totalReturn",
    getValue: (r) => r.totalReturn,
    format: (v) => `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`,
    colorFn: (v) => (v >= 0 ? "text-emerald-400" : "text-red-400"),
    higherIsBetter: true,
  },
  {
    label: "Win Rate",
    key: "winRate",
    getValue: (r) => r.winRate,
    format: (v) => `${v.toFixed(1)}%`,
    colorFn: (v) => (v >= 50 ? "text-emerald-400" : "text-red-400"),
    higherIsBetter: true,
  },
  {
    label: "Sharpe Ratio",
    key: "sharpeRatio",
    getValue: (r) => r.sharpeRatio,
    format: (v) => v.toFixed(2),
    colorFn: (v) => (v >= 1 ? "text-emerald-400" : "text-amber-400"),
    higherIsBetter: true,
  },
  {
    label: "Max Drawdown",
    key: "maxDrawdown",
    getValue: (r) => r.maxDrawdown,
    format: (v) => `${v.toFixed(2)}%`,
    colorFn: (v) => {
      if (v <= 5) return "text-red-300";
      if (v <= 15) return "text-red-400";
      if (v <= 30) return "text-red-500";
      return "text-red-600";
    },
    higherIsBetter: false,
  },
  {
    label: "Profit Factor",
    key: "profitFactor",
    getValue: (r) => r.profitFactor,
    format: (v) => v.toFixed(2),
    colorFn: (v) => (v >= 1 ? "text-emerald-400" : "text-red-400"),
    higherIsBetter: true,
  },
  {
    label: "Total Trades",
    key: "totalTrades",
    getValue: (r) => r.totalTrades,
    format: (v) => v.toLocaleString(),
    colorFn: () => "text-muted-foreground",
    higherIsBetter: true,
  },
  {
    label: "Avg Win",
    key: "avgWin",
    getValue: (r) => r.avgWin,
    format: (v) => `+${v.toFixed(2)}%`,
    colorFn: () => "text-emerald-400",
    higherIsBetter: true,
  },
  {
    label: "Avg Loss",
    key: "avgLoss",
    getValue: (r) => r.avgLoss,
    format: (v) => `${v.toFixed(2)}%`,
    colorFn: () => "text-red-400",
    higherIsBetter: false,
  },
  {
    label: "Risk-Adj Return",
    key: "riskAdjusted",
    getValue: (r) => (r.maxDrawdown !== 0 ? r.totalReturn / r.maxDrawdown : 0),
    format: (v) => v.toFixed(2),
    colorFn: (v) => (v >= 1 ? "text-emerald-400" : "text-amber-400"),
    higherIsBetter: true,
  },
];

function findBestIndex(
  values: number[],
  higherIsBetter: boolean
): number {
  if (values.length === 0) return -1;
  let bestIdx = 0;
  for (let i = 1; i < values.length; i++) {
    if (higherIsBetter ? values[i] > values[bestIdx] : values[i] < values[bestIdx]) {
      bestIdx = i;
    }
  }
  return bestIdx;
}

export function ComparisonTable({ results }: ComparisonTableProps) {
  const { winCounts, overallWinnerIdx } = useMemo(() => {
    const counts = new Array(results.length).fill(0);

    for (const metric of metrics) {
      const values = results.map(metric.getValue);
      const bestIdx = findBestIndex(values, metric.higherIsBetter);
      if (bestIdx >= 0) {
        counts[bestIdx]++;
      }
    }

    let winnerIdx = 0;
    for (let i = 1; i < counts.length; i++) {
      if (counts[i] > counts[winnerIdx]) {
        winnerIdx = i;
      }
    }

    return { winCounts: counts, overallWinnerIdx: winnerIdx };
  }, [results]);

  if (results.length === 0) {
    return (
      <Card className="bg-card/50 border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <BarChart3 className="h-5 w-5" />
            Strategy Comparison
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No backtest results to compare. Run at least two strategies to see a
            comparison.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card/50 border-border/50">
      <CardHeader>
        <div className="flex items-center gap-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            <BarChart3 className="h-5 w-5" />
            Strategy Comparison
          </CardTitle>
          <Badge variant="secondary" className="text-xs">
            {results.length} {results.length === 1 ? "strategy" : "strategies"}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto -mx-6 px-6">
          <table className="w-full min-w-[600px] border-collapse">
            <thead>
              <tr className="border-b border-border/50">
                <th className="py-3 pr-4 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Metric
                </th>
                {results.map((r, i) => (
                  <th
                    key={i}
                    className={cn(
                      "py-3 px-4 text-center text-sm font-bold",
                      i === overallWinnerIdx && "text-amber-400"
                    )}
                  >
                    <div className="flex flex-col items-center gap-1">
                      <span>{r.strategy}</span>
                      <span className="text-xs font-normal text-muted-foreground">
                        {r.asset} &middot; {r.period}d
                      </span>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {metrics.map((metric) => {
                const values = results.map(metric.getValue);
                const bestIdx = findBestIndex(values, metric.higherIsBetter);

                return (
                  <tr
                    key={metric.key}
                    className="border-b border-border/30 last:border-0 hover:bg-muted/20 transition-colors"
                  >
                    <td className="py-2.5 pr-4 text-sm text-muted-foreground whitespace-nowrap">
                      {metric.label}
                    </td>
                    {results.map((r, i) => {
                      const value = metric.getValue(r);
                      const isBest = i === bestIdx && results.length > 1;

                      return (
                        <td
                          key={i}
                          className={cn(
                            "py-2.5 px-4 text-center font-mono text-sm",
                            metric.colorFn(value),
                            isBest && "font-semibold"
                          )}
                        >
                          <div className="flex items-center justify-center gap-1.5">
                            <span>{metric.format(value)}</span>
                            {isBest && (
                              <Crown className="h-3.5 w-3.5 text-amber-400 flex-shrink-0" />
                            )}
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Overall Winner */}
        {results.length > 1 && (
          <div className="mt-6 flex items-center justify-center gap-3 rounded-lg border border-amber-500/20 bg-amber-500/5 py-3 px-4">
            <Trophy className="h-5 w-5 text-amber-400" />
            <div className="flex items-center gap-2 text-sm">
              <span className="text-muted-foreground">Overall Winner:</span>
              <span className="font-bold text-amber-400">
                {results[overallWinnerIdx].strategy}
              </span>
              <Badge
                variant="outline"
                className="border-amber-500/30 text-amber-400 text-xs"
              >
                {winCounts[overallWinnerIdx]} / {metrics.length} metrics
              </Badge>
            </div>
            {winCounts[overallWinnerIdx] >= metrics.length * 0.7 ? (
              <TrendingUp className="h-4 w-4 text-emerald-400" />
            ) : (
              <TrendingDown className="h-4 w-4 text-muted-foreground" />
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
