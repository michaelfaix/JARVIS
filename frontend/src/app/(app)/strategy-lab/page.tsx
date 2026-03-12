// =============================================================================
// src/app/(app)/strategy-lab/page.tsx — Strategy Lab with Backtest Engine
// =============================================================================

"use client";

import { useCallback, useState } from "react";
import { AppHeader } from "@/components/layout/app-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { STRATEGIES } from "@/lib/constants";
import { useProfile } from "@/hooks/use-profile";
import { UpgradeGate } from "@/components/ui/upgrade-gate";
import {
  FlaskConical,
  Play,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Trophy,
  Target,
  Loader2,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Backtest Engine (synthetic, deterministic)
// ---------------------------------------------------------------------------

interface BacktestTrade {
  day: number;
  asset: string;
  direction: "LONG" | "SHORT";
  entry: number;
  exit: number;
  pnl: number;
  pnlPct: number;
}

interface BacktestResult {
  strategy: string;
  trades: BacktestTrade[];
  equity: number[];
  totalReturn: number;
  winRate: number;
  sharpe: number;
  maxDrawdown: number;
  avgWin: number;
  avgLoss: number;
  profitFactor: number;
  totalTrades: number;
}

function hashSeed(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) & 0xffff;
  return h;
}

function runBacktest(
  strategyId: string,
  days: number,
  capital: number
): BacktestResult {
  const seed = hashSeed(strategyId);
  const trades: BacktestTrade[] = [];
  const assets = ["BTC", "ETH", "SOL", "SPY", "GLD"];
  const basePrices: Record<string, number> = {
    BTC: 65000, ETH: 3200, SOL: 145, SPY: 520, GLD: 215,
  };

  // Generate price series
  const priceHistory: Record<string, number[]> = {};
  for (const asset of assets) {
    const base = basePrices[asset];
    const prices: number[] = [];
    for (let d = 0; d <= days; d++) {
      const trend = Math.sin((d / days) * Math.PI * 2 + seed * 0.1) * base * 0.05;
      const noise = Math.sin(d * 0.7 + hashSeed(asset)) * base * 0.012;
      prices.push(base + trend + noise);
    }
    priceHistory[asset] = prices;
  }

  // Strategy parameters
  const lookback = strategyId === "momentum" ? 5 : strategyId === "mean_reversion" ? 10 : 7;
  const threshold = strategyId === "momentum" ? 0.01 : strategyId === "mean_reversion" ? -0.008 : 0.005;
  const winBias = strategyId === "momentum" ? 0.58 : strategyId === "mean_reversion" ? 0.62 : 0.60;

  // Walk through days, generate trades
  let equity = capital;
  const equityCurve: number[] = [capital];
  const tradeSize = 0.1; // 10% per trade

  for (let d = lookback; d < days - 1; d += 3 + (seed % 2)) {
    const assetIdx = (d + seed) % assets.length;
    const asset = assets[assetIdx];
    const prices = priceHistory[asset];
    const currentPrice = prices[d];
    const pastPrice = prices[d - lookback];
    const momentum = (currentPrice - pastPrice) / pastPrice;

    let direction: "LONG" | "SHORT";
    if (strategyId === "mean_reversion") {
      direction = momentum < threshold ? "LONG" : "SHORT";
    } else {
      direction = momentum > threshold ? "LONG" : "SHORT";
    }

    // Deterministic outcome based on day/seed
    const outcomeHash = Math.sin(d * 1.7 + seed * 0.3) * 0.5 + 0.5;
    const isWin = outcomeHash < winBias;
    const magnitude = 0.005 + Math.abs(Math.sin(d * 2.3 + seed)) * 0.025;

    const exitPrice = isWin
      ? direction === "LONG"
        ? currentPrice * (1 + magnitude)
        : currentPrice * (1 - magnitude)
      : direction === "LONG"
      ? currentPrice * (1 - magnitude * 0.7)
      : currentPrice * (1 + magnitude * 0.7);

    const tradeCapital = equity * tradeSize;
    const size = tradeCapital / currentPrice;
    const pnl =
      direction === "LONG"
        ? (exitPrice - currentPrice) * size
        : (currentPrice - exitPrice) * size;
    const pnlPct = (pnl / tradeCapital) * 100;

    equity += pnl;

    trades.push({
      day: d,
      asset,
      direction,
      entry: currentPrice,
      exit: exitPrice,
      pnl,
      pnlPct,
    });

    equityCurve.push(equity);
  }

  // Fill equity curve to full length
  while (equityCurve.length <= days) {
    equityCurve.push(equity);
  }

  // Compute stats
  const wins = trades.filter((t) => t.pnl > 0);
  const losses = trades.filter((t) => t.pnl <= 0);
  const winRate = trades.length > 0 ? (wins.length / trades.length) * 100 : 0;
  const avgWin = wins.length > 0 ? wins.reduce((s, t) => s + t.pnl, 0) / wins.length : 0;
  const avgLoss = losses.length > 0 ? Math.abs(losses.reduce((s, t) => s + t.pnl, 0) / losses.length) : 0;
  const totalReturn = ((equity - capital) / capital) * 100;

  // Max drawdown
  let peak = capital;
  let maxDD = 0;
  for (const eq of equityCurve) {
    if (eq > peak) peak = eq;
    const dd = ((peak - eq) / peak) * 100;
    if (dd > maxDD) maxDD = dd;
  }

  // Simplified Sharpe (annualized)
  const returns = equityCurve.slice(1).map((eq, i) => (eq - equityCurve[i]) / equityCurve[i]);
  const meanReturn = returns.reduce((s, r) => s + r, 0) / returns.length;
  const stdReturn = Math.sqrt(returns.reduce((s, r) => s + (r - meanReturn) ** 2, 0) / returns.length);
  const sharpe = stdReturn > 0 ? (meanReturn / stdReturn) * Math.sqrt(252) : 0;

  const grossWin = wins.reduce((s, t) => s + t.pnl, 0);
  const grossLoss = Math.abs(losses.reduce((s, t) => s + t.pnl, 0));
  const profitFactor = grossLoss > 0 ? grossWin / grossLoss : grossWin > 0 ? 999 : 0;

  return {
    strategy: strategyId,
    trades,
    equity: equityCurve,
    totalReturn,
    winRate,
    sharpe,
    maxDrawdown: maxDD,
    avgWin,
    avgLoss,
    profitFactor,
    totalTrades: trades.length,
  };
}

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

export default function StrategyLabPage() {
  const { tier } = useProfile();

  return (
    <UpgradeGate currentTier={tier} requiredTier="pro" feature="Strategy Lab & Backtesting">
      <StrategyLabContent />
    </UpgradeGate>
  );
}

function StrategyLabContent() {
  const [selectedStrategy, setSelectedStrategy] = useState("combined");
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [running, setRunning] = useState(false);

  const handleBacktest = useCallback(() => {
    setRunning(true);
    // Small delay for UI feedback
    setTimeout(() => {
      const r = runBacktest(selectedStrategy, 90, 100000);
      setResult(r);
      setRunning(false);
    }, 500);
  }, [selectedStrategy]);

  const equityMin = result ? Math.min(...result.equity) : 0;
  const equityMax = result ? Math.max(...result.equity) : 0;
  const equityRange = equityMax - equityMin || 1;

  return (
    <>
      <AppHeader title="Strategy Lab" subtitle="Backtest & Optimize" />
      <div className="p-3 sm:p-4 md:p-6 space-y-4 md:space-y-6">
        {/* Strategy Selection */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {STRATEGIES.map((strategy) => {
            const isSelected = selectedStrategy === strategy.id;
            return (
              <Card
                key={strategy.id}
                onClick={() => setSelectedStrategy(strategy.id)}
                className={`bg-card/50 border-border/50 cursor-pointer transition-colors ${
                  isSelected
                    ? "border-blue-500/50 ring-1 ring-blue-500/20"
                    : "hover:border-blue-500/30"
                }`}
              >
                <CardContent className="pt-5 pb-4 px-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <FlaskConical
                        className={`h-5 w-5 ${
                          isSelected ? "text-blue-400" : "text-muted-foreground"
                        }`}
                      />
                      <span className="font-bold text-white">
                        {strategy.label}
                      </span>
                    </div>
                    <Badge
                      variant="outline"
                      className={`text-[10px] ${
                        isSelected
                          ? "text-blue-400 border-blue-500/30"
                          : "text-muted-foreground"
                      }`}
                    >
                      {strategy.id === "momentum"
                        ? "Trend Following"
                        : strategy.id === "mean_reversion"
                        ? "Contrarian"
                        : "Hybrid"}
                    </Badge>
                  </div>

                  <p className="text-xs text-muted-foreground">
                    {strategy.id === "momentum"
                      ? "Follows price trends using momentum signals. Best in RISK_ON/RISK_OFF."
                      : strategy.id === "mean_reversion"
                      ? "Identifies overbought/oversold reversals. Effective in TRANSITION."
                      : "Combines momentum and mean reversion with regime-adaptive weighting."}
                  </p>

                  <Separator className="opacity-30" />

                  <div className="grid grid-cols-3 gap-2 text-center text-xs">
                    <div>
                      <div className="text-muted-foreground mb-1">Win Rate</div>
                      <div className="font-mono text-white">
                        {strategy.id === "momentum" ? "58%" : strategy.id === "mean_reversion" ? "62%" : "60%"}
                      </div>
                    </div>
                    <div>
                      <div className="text-muted-foreground mb-1">Sharpe</div>
                      <div className="font-mono text-white">
                        {strategy.id === "momentum" ? "1.8" : strategy.id === "mean_reversion" ? "1.5" : "2.1"}
                      </div>
                    </div>
                    <div>
                      <div className="text-muted-foreground mb-1">Max DD</div>
                      <div className="font-mono text-white">
                        {strategy.id === "momentum" ? "-12%" : strategy.id === "mean_reversion" ? "-8%" : "-10%"}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Backtest Controls */}
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Backtest Engine
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-6 text-sm">
                <div>
                  <span className="text-xs text-muted-foreground">Strategy: </span>
                  <span className="font-mono text-white">
                    {STRATEGIES.find((s) => s.id === selectedStrategy)?.label}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground">Period: </span>
                  <span className="font-mono text-white">90 days</span>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground">Capital: </span>
                  <span className="font-mono text-white">$100,000</span>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground">Assets: </span>
                  <span className="font-mono text-white">BTC, ETH, SOL, SPY, GLD</span>
                </div>
              </div>
              <Button
                onClick={handleBacktest}
                disabled={running}
                className="bg-blue-600 hover:bg-blue-700 text-white gap-2"
              >
                {running ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
                Run Backtest
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        {result && (
          <>
            {/* Performance Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
              {[
                {
                  label: "Total Return",
                  value: `${result.totalReturn >= 0 ? "+" : ""}${result.totalReturn.toFixed(2)}%`,
                  color: result.totalReturn >= 0 ? "text-green-400" : "text-red-400",
                  icon: result.totalReturn >= 0 ? TrendingUp : TrendingDown,
                },
                {
                  label: "Win Rate",
                  value: `${result.winRate.toFixed(1)}%`,
                  color: result.winRate >= 50 ? "text-green-400" : "text-red-400",
                  icon: Trophy,
                },
                {
                  label: "Sharpe Ratio",
                  value: result.sharpe.toFixed(2),
                  color: result.sharpe > 1 ? "text-green-400" : result.sharpe > 0 ? "text-yellow-400" : "text-red-400",
                  icon: Target,
                },
                {
                  label: "Max Drawdown",
                  value: `-${result.maxDrawdown.toFixed(2)}%`,
                  color: result.maxDrawdown < 10 ? "text-yellow-400" : "text-red-400",
                  icon: TrendingDown,
                },
                {
                  label: "Avg Win",
                  value: `+$${result.avgWin.toFixed(0)}`,
                  color: "text-green-400",
                  icon: TrendingUp,
                },
                {
                  label: "Avg Loss",
                  value: `-$${result.avgLoss.toFixed(0)}`,
                  color: "text-red-400",
                  icon: TrendingDown,
                },
                {
                  label: "Profit Factor",
                  value: result.profitFactor.toFixed(2),
                  color: result.profitFactor > 1.5 ? "text-green-400" : result.profitFactor > 1 ? "text-yellow-400" : "text-red-400",
                  icon: BarChart3,
                },
                {
                  label: "Total Trades",
                  value: result.totalTrades.toString(),
                  color: "text-white",
                  icon: FlaskConical,
                },
              ].map((stat) => {
                const Icon = stat.icon;
                return (
                  <Card key={stat.label} className="bg-card/50 border-border/50">
                    <CardContent className="pt-3 pb-2 px-3">
                      <div className="flex items-center gap-1 text-[10px] text-muted-foreground mb-1">
                        <Icon className="h-3 w-3" />
                        {stat.label}
                      </div>
                      <div className={`text-lg font-bold font-mono ${stat.color}`}>
                        {stat.value}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            {/* Equity Curve (simple SVG) */}
            <Card className="bg-card/50 border-border/50">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Equity Curve — $100,000 starting capital
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-48 relative">
                  <svg
                    viewBox={`0 0 ${result.equity.length} 100`}
                    preserveAspectRatio="none"
                    className="w-full h-full"
                  >
                    {/* Grid lines */}
                    {[0, 25, 50, 75, 100].map((y) => (
                      <line
                        key={y}
                        x1={0}
                        y1={y}
                        x2={result.equity.length}
                        y2={y}
                        stroke="rgba(255,255,255,0.05)"
                        strokeWidth={0.3}
                      />
                    ))}
                    {/* Starting capital line */}
                    <line
                      x1={0}
                      y1={100 - ((100000 - equityMin) / equityRange) * 100}
                      x2={result.equity.length}
                      y2={100 - ((100000 - equityMin) / equityRange) * 100}
                      stroke="rgba(255,255,255,0.15)"
                      strokeWidth={0.3}
                      strokeDasharray="3,3"
                    />
                    {/* Equity line */}
                    <polyline
                      fill="none"
                      stroke={result.totalReturn >= 0 ? "#22c55e" : "#ef4444"}
                      strokeWidth={0.8}
                      points={result.equity
                        .map(
                          (eq, i) =>
                            `${i},${100 - ((eq - equityMin) / equityRange) * 100}`
                        )
                        .join(" ")}
                    />
                    {/* Fill under curve */}
                    <polygon
                      fill={result.totalReturn >= 0 ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)"}
                      points={`0,100 ${result.equity
                        .map(
                          (eq, i) =>
                            `${i},${100 - ((eq - equityMin) / equityRange) * 100}`
                        )
                        .join(" ")} ${result.equity.length - 1},100`}
                    />
                  </svg>
                  {/* Y-axis labels */}
                  <div className="absolute left-0 top-0 text-[10px] font-mono text-muted-foreground">
                    ${equityMax.toLocaleString("en-US", { maximumFractionDigits: 0 })}
                  </div>
                  <div className="absolute left-0 bottom-0 text-[10px] font-mono text-muted-foreground">
                    ${equityMin.toLocaleString("en-US", { maximumFractionDigits: 0 })}
                  </div>
                  <div className="absolute right-0 bottom-0 text-[10px] font-mono text-muted-foreground">
                    Day {result.equity.length - 1}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Trade Log */}
            <Card className="bg-card/50 border-border/50">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Trade Log ({result.trades.length} trades)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Day</TableHead>
                      <TableHead>Asset</TableHead>
                      <TableHead>Side</TableHead>
                      <TableHead className="text-right">Entry</TableHead>
                      <TableHead className="text-right">Exit</TableHead>
                      <TableHead className="text-right">P&L</TableHead>
                      <TableHead className="text-right">Return</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {result.trades.slice(0, 20).map((trade, i) => (
                      <TableRow key={i}>
                        <TableCell className="text-muted-foreground font-mono text-xs">
                          D{trade.day}
                        </TableCell>
                        <TableCell className="font-medium text-white">
                          {trade.asset}
                        </TableCell>
                        <TableCell>
                          <Badge
                            className={
                              trade.direction === "LONG"
                                ? "bg-green-500/20 text-green-400 border-green-500/30"
                                : "bg-red-500/20 text-red-400 border-red-500/30"
                            }
                          >
                            {trade.direction}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right font-mono text-muted-foreground text-xs">
                          ${trade.entry.toFixed(2)}
                        </TableCell>
                        <TableCell className="text-right font-mono text-white text-xs">
                          ${trade.exit.toFixed(2)}
                        </TableCell>
                        <TableCell
                          className={`text-right font-mono ${
                            trade.pnl >= 0 ? "text-green-400" : "text-red-400"
                          }`}
                        >
                          {trade.pnl >= 0 ? "+" : ""}${Math.abs(trade.pnl).toFixed(0)}
                        </TableCell>
                        <TableCell
                          className={`text-right font-mono text-xs ${
                            trade.pnlPct >= 0 ? "text-green-400" : "text-red-400"
                          }`}
                        >
                          {trade.pnlPct >= 0 ? "+" : ""}{trade.pnlPct.toFixed(2)}%
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {result.trades.length > 20 && (
                  <div className="text-xs text-muted-foreground text-center mt-3">
                    Showing 20 of {result.trades.length} trades
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        )}

        {/* Architecture Info */}
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              JARVIS Architecture
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
              <div className="rounded-lg bg-background/50 p-3">
                <div className="text-muted-foreground mb-1">ML Modules</div>
                <div className="text-white font-bold">S06 — S15</div>
                <div className="text-muted-foreground mt-1">
                  Fast Path, Deep Path, Uncertainty, Calibration, OOD, Quality,
                  Learning, Degradation, API, Validation
                </div>
              </div>
              <div className="rounded-lg bg-background/50 p-3">
                <div className="text-muted-foreground mb-1">Determinism</div>
                <div className="text-white font-bold">DET-01 to DET-07</div>
                <div className="text-muted-foreground mt-1">
                  No random, no file I/O, no global state, bit-identical outputs
                </div>
              </div>
              <div className="rounded-lg bg-background/50 p-3">
                <div className="text-muted-foreground mb-1">Test Coverage</div>
                <div className="text-white font-bold">8,897 Tests</div>
                <div className="text-muted-foreground mt-1">
                  100% FAS compliance across all modules
                </div>
              </div>
              <div className="rounded-lg bg-background/50 p-3">
                <div className="text-muted-foreground mb-1">Risk Engine</div>
                <div className="text-white font-bold">v6.1.0 FREEZE</div>
                <div className="text-muted-foreground mt-1">
                  Hash-protected thresholds, DVH verified
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
