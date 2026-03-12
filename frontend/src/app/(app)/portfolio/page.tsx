// =============================================================================
// src/app/(app)/portfolio/page.tsx — Paper Trading Portfolio
// =============================================================================

"use client";

import React, { useEffect } from "react";
import { AppHeader } from "@/components/layout/app-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Separator } from "@/components/ui/separator";
import { usePortfolio } from "@/hooks/use-portfolio";
import { useSystemStatus } from "@/hooks/use-jarvis";
import { usePrices } from "@/hooks/use-prices";
import { inferRegime, REGIME_COLORS, type RegimeState } from "@/lib/types";
import { useToast } from "@/components/ui/toast";
import { EquityCurve } from "@/components/chart/equity-curve";
import { useAchievements } from "@/hooks/use-achievements";
import { useNotifications } from "@/hooks/use-notifications";
import { Progress } from "@/components/ui/progress";
import {
  TrendingUp,
  TrendingDown,
  Wallet,
  ShieldAlert,
  Wifi,
  WifiOff,
  Trophy,
  BarChart3,
  LineChart,
  Star,
  X,
  Download,
} from "lucide-react";

export default function PortfolioPage() {
  const {
    state,
    closePosition,
    updatePrices,
    resetPortfolio,
    unrealizedPnl,
    totalValue,
    winRate,
    avgWin,
    avgLoss,
    drawdown,
  } = usePortfolio();
  const { status } = useSystemStatus(5000);
  const regime: RegimeState = status ? inferRegime(status.modus) : "RISK_ON";
  const { prices, binanceConnected } = usePrices(5000);
  const { toast } = useToast();
  const { push: pushNotification } = useNotifications();

  const prevUnlockedRef = React.useRef<Set<string>>(new Set());

  const achievements = useAchievements(
    state.closedTrades,
    totalValue,
    state.totalCapital,
    winRate,
    drawdown
  );
  const unlockedCount = achievements.filter((a) => a.unlocked).length;

  // Notify on newly unlocked achievements
  useEffect(() => {
    const currentUnlocked = new Set(achievements.filter((a) => a.unlocked).map((a) => a.id));
    const prev = prevUnlockedRef.current;
    if (prev.size > 0) {
      for (const ach of achievements) {
        if (ach.unlocked && !prev.has(ach.id)) {
          pushNotification(
            "achievement",
            `${ach.icon} ${ach.title} Unlocked!`,
            ach.description
          );
        }
      }
    }
    prevUnlockedRef.current = currentUnlocked;
  }, [achievements, pushNotification]);

  // Update position prices whenever live prices change
  useEffect(() => {
    if (state.positions.length > 0) {
      updatePrices(prices);
    }
  }, [prices, state.positions.length, updatePrices]);

  const totalPnl = state.realizedPnl + unrealizedPnl;
  const totalPnlPercent =
    state.totalCapital > 0 ? (totalPnl / state.totalCapital) * 100 : 0;

  // Risk score from system status
  const riskScore = status
    ? Math.min(
        100,
        Math.round(
          (status.ece * 200 +
            status.ood_score * 100 +
            status.meta_unsicherheit * 100) /
            3
        )
      )
    : 0;

  // Allocation by asset
  const allocation = state.positions.reduce<Record<string, number>>(
    (acc, pos) => {
      acc[pos.asset] = (acc[pos.asset] || 0) + pos.capitalAllocated;
      return acc;
    },
    {}
  );
  const allocatedTotal = Object.values(allocation).reduce(
    (sum, v) => sum + v,
    0
  );

  return (
    <>
      <AppHeader title="Portfolio" subtitle="Paper Trading Account" />
      <div className="p-3 sm:p-4 md:p-6 space-y-4 md:space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                <Wallet className="h-3 w-3" /> Total Value
              </div>
              <div className="text-2xl font-bold font-mono text-white">
                $
                {totalValue.toLocaleString("en-US", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                {totalPnl >= 0 ? (
                  <TrendingUp className="h-3 w-3" />
                ) : (
                  <TrendingDown className="h-3 w-3" />
                )}
                Total P&L
              </div>
              <div
                className={`text-2xl font-bold font-mono ${
                  totalPnl >= 0 ? "text-green-400" : "text-red-400"
                }`}
              >
                {totalPnl >= 0 ? "+" : ""}$
                {Math.abs(totalPnl).toLocaleString("en-US", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </div>
              <div
                className={`text-xs font-mono ${
                  totalPnlPercent >= 0 ? "text-green-400" : "text-red-400"
                }`}
              >
                {totalPnlPercent >= 0 ? "+" : ""}
                {totalPnlPercent.toFixed(2)}%
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                <ShieldAlert className="h-3 w-3" /> Risk Score
              </div>
              <div
                className={`text-2xl font-bold font-mono ${
                  riskScore < 30
                    ? "text-green-400"
                    : riskScore < 60
                    ? "text-yellow-400"
                    : "text-red-400"
                }`}
              >
                {riskScore}
              </div>
              <div className="text-xs text-muted-foreground">
                {riskScore < 30
                  ? "Low Risk"
                  : riskScore < 60
                  ? "Moderate"
                  : "High Risk"}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="text-xs text-muted-foreground mb-1">
                Available Capital
              </div>
              <div className="text-2xl font-bold font-mono text-white">
                $
                {state.availableCapital.toLocaleString("en-US", {
                  minimumFractionDigits: 0,
                })}
              </div>
              <div className="text-xs text-muted-foreground">
                of ${state.totalCapital.toLocaleString()}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                {binanceConnected ? (
                  <Wifi className="h-3 w-3 text-green-400" />
                ) : (
                  <WifiOff className="h-3 w-3 text-yellow-500" />
                )}
                Price Feed
              </div>
              <div className="text-sm font-mono text-white">
                {binanceConnected ? (
                  <span className="text-green-400">Binance Live</span>
                ) : (
                  <span className="text-yellow-400">Synthetic</span>
                )}
              </div>
              <div className="text-[10px] text-muted-foreground">
                Updates every 5s
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Asset Allocation */}
          <Card className="bg-card/50 border-border/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Asset Allocation
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {Object.entries(allocation).length === 0 ? (
                <div className="text-sm text-muted-foreground py-4 text-center">
                  No open positions
                </div>
              ) : (
                Object.entries(allocation).map(([asset, amount]) => {
                  const pct =
                    allocatedTotal > 0 ? (amount / allocatedTotal) * 100 : 0;
                  return (
                    <div key={asset}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-white font-medium">{asset}</span>
                        <span className="font-mono text-muted-foreground">
                          {pct.toFixed(1)}%
                        </span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-background/50 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-blue-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })
              )}
              <Separator className="opacity-50" />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Cash</span>
                <span className="font-mono">
                  $
                  {state.availableCapital.toLocaleString("en-US", {
                    minimumFractionDigits: 0,
                  })}
                </span>
              </div>
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Market Regime</span>
                <Badge
                  variant="outline"
                  className="text-[10px] px-1.5 py-0"
                  style={{
                    borderColor: REGIME_COLORS[regime],
                    color: REGIME_COLORS[regime],
                  }}
                >
                  {regime.replace("_", " ")}
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Open Positions Table */}
          <Card className="bg-card/50 border-border/50 lg:col-span-2">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Open Positions ({state.positions.length})
                </CardTitle>
                <div className="flex items-center gap-2">
                  {state.closedTrades.length > 0 && (
                    <span className="text-[10px] text-muted-foreground font-mono">
                      Win Rate: {winRate.toFixed(0)}%
                    </span>
                  )}
                  {state.positions.length > 0 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-xs text-muted-foreground h-7"
                      onClick={() => {
                        resetPortfolio(state.totalCapital);
                        toast("warning", "All positions closed");
                      }}
                    >
                      Close All
                    </Button>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Asset</TableHead>
                      <TableHead>Side</TableHead>
                      <TableHead className="text-right">Size</TableHead>
                      <TableHead className="text-right">Entry</TableHead>
                      <TableHead className="text-right">Current</TableHead>
                      <TableHead className="text-right">P&L</TableHead>
                      <TableHead></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {state.positions.length === 0 ? (
                      <TableRow>
                        <TableCell
                          colSpan={7}
                          className="text-center text-muted-foreground py-8"
                        >
                          No open positions. Accept signals to open trades.
                        </TableCell>
                      </TableRow>
                    ) : (
                      state.positions.map((pos) => (
                        <TableRow key={pos.id}>
                          <TableCell className="font-medium text-white">
                            {pos.asset}
                          </TableCell>
                          <TableCell>
                            <Badge
                              className={
                                pos.direction === "LONG"
                                  ? "bg-green-500/20 text-green-400 border-green-500/30"
                                  : "bg-red-500/20 text-red-400 border-red-500/30"
                              }
                            >
                              {pos.direction}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right font-mono text-white">
                            {pos.size.toFixed(4)}
                          </TableCell>
                          <TableCell className="text-right font-mono text-muted-foreground">
                            ${pos.entryPrice.toLocaleString()}
                          </TableCell>
                          <TableCell className="text-right font-mono text-white">
                            ${pos.currentPrice.toLocaleString()}
                          </TableCell>
                          <TableCell
                            className={`text-right font-mono ${
                              pos.pnl >= 0 ? "text-green-400" : "text-red-400"
                            }`}
                          >
                            {pos.pnl >= 0 ? "+" : ""}$
                            {Math.abs(pos.pnl).toFixed(2)}
                            <div className="text-[10px]">
                              {pos.pnlPercent >= 0 ? "+" : ""}
                              {pos.pnlPercent.toFixed(2)}%
                            </div>
                          </TableCell>
                          <TableCell>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 w-7 p-0 text-muted-foreground hover:text-red-400"
                              onClick={() => {
                                const pnl = pos.direction === "LONG"
                                  ? (pos.currentPrice - pos.entryPrice) * pos.size
                                  : (pos.entryPrice - pos.currentPrice) * pos.size;
                                closePosition(pos.id);
                                toast("info", `Closed ${pos.asset} position`);
                                pushNotification(
                                  "trade",
                                  `${pos.asset} Position Closed`,
                                  `${pnl >= 0 ? "+" : ""}$${pnl.toFixed(2)} P&L`
                                );
                              }}
                            >
                              <X className="h-3 w-3" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Trade Stats */}
        {state.closedTrades.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <Card className="bg-card/50 border-border/50">
              <CardContent className="pt-4 pb-3 px-4">
                <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                  <Trophy className="h-3 w-3" /> Win Rate
                </div>
                <div className={`text-xl font-bold font-mono ${winRate >= 50 ? "text-green-400" : "text-red-400"}`}>
                  {winRate.toFixed(1)}%
                </div>
              </CardContent>
            </Card>
            <Card className="bg-card/50 border-border/50">
              <CardContent className="pt-4 pb-3 px-4">
                <div className="text-xs text-muted-foreground mb-1">Total Trades</div>
                <div className="text-xl font-bold font-mono text-white">
                  {state.closedTrades.length}
                </div>
              </CardContent>
            </Card>
            <Card className="bg-card/50 border-border/50">
              <CardContent className="pt-4 pb-3 px-4">
                <div className="text-xs text-muted-foreground mb-1">Avg Win</div>
                <div className="text-xl font-bold font-mono text-green-400">
                  +${avgWin.toFixed(0)}
                </div>
              </CardContent>
            </Card>
            <Card className="bg-card/50 border-border/50">
              <CardContent className="pt-4 pb-3 px-4">
                <div className="text-xs text-muted-foreground mb-1">Avg Loss</div>
                <div className="text-xl font-bold font-mono text-red-400">
                  ${avgLoss.toFixed(0)}
                </div>
              </CardContent>
            </Card>
            <Card className="bg-card/50 border-border/50">
              <CardContent className="pt-4 pb-3 px-4">
                <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                  <BarChart3 className="h-3 w-3" /> Drawdown
                </div>
                <div className={`text-xl font-bold font-mono ${drawdown > 5 ? "text-red-400" : drawdown > 0 ? "text-yellow-400" : "text-green-400"}`}>
                  {drawdown.toFixed(2)}%
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Equity Curve */}
        {state.closedTrades.length >= 2 && (
          <Card className="bg-card/50 border-border/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <LineChart className="h-4 w-4" />
                Equity Curve
              </CardTitle>
            </CardHeader>
            <CardContent>
              <EquityCurve
                closedTrades={state.closedTrades}
                initialCapital={state.totalCapital}
                currentValue={totalValue}
                height={220}
                benchmarks={[
                  { label: "BTC", color: "#f7931a", returnPct: 12.5 },
                  { label: "SPY", color: "#6366f1", returnPct: 8.2 },
                ]}
              />
            </CardContent>
          </Card>
        )}

        {/* Achievements */}
        {state.closedTrades.length > 0 && (
          <Card className="bg-card/50 border-border/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <Star className="h-4 w-4" />
                Achievements
                <Badge variant="outline" className="ml-auto text-[10px]">
                  {unlockedCount}/{achievements.length} unlocked
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {achievements.map((ach) => {
                  const tierColor =
                    ach.tier === "gold"
                      ? "border-yellow-500/30 bg-yellow-500/5"
                      : ach.tier === "silver"
                      ? "border-gray-400/30 bg-gray-400/5"
                      : "border-amber-700/30 bg-amber-700/5";

                  return (
                    <div
                      key={ach.id}
                      className={`rounded-lg border p-3 ${
                        ach.unlocked
                          ? tierColor
                          : "border-border/30 bg-background/30 opacity-60"
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className="text-lg">{ach.icon}</span>
                        <span className="text-xs font-medium text-white truncate">
                          {ach.title}
                        </span>
                      </div>
                      <div className="text-[10px] text-muted-foreground mb-2">
                        {ach.description}
                      </div>
                      <Progress
                        value={ach.progress}
                        className="h-1"
                        indicatorClassName={
                          ach.unlocked
                            ? ach.tier === "gold"
                              ? "bg-yellow-500"
                              : ach.tier === "silver"
                              ? "bg-gray-400"
                              : "bg-amber-700"
                            : "bg-muted-foreground/50"
                        }
                      />
                      {ach.unlocked && (
                        <div className="text-[9px] text-green-400 mt-1">
                          Unlocked
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Trade History */}
        {state.closedTrades.length > 0 && (
          <Card className="bg-card/50 border-border/50">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Trade Journal ({state.closedTrades.length})
                </CardTitle>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 text-xs gap-1"
                  onClick={() => {
                    const header = "Asset,Direction,Entry Price,Exit Price,Size,Capital,P&L,Return %,Opened,Closed\n";
                    const rows = state.closedTrades
                      .map(
                        (t) =>
                          `${t.asset},${t.direction},${t.entryPrice},${t.exitPrice},${t.size},${t.capitalAllocated},${t.pnl.toFixed(2)},${t.pnlPercent.toFixed(2)},${t.openedAt},${t.closedAt}`
                      )
                      .join("\n");
                    const blob = new Blob([header + rows], { type: "text/csv" });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = `jarvis-trades-${new Date().toISOString().slice(0, 10)}.csv`;
                    a.click();
                    URL.revokeObjectURL(url);
                    toast("success", "Trade journal exported as CSV");
                  }}
                >
                  <Download className="h-3 w-3" />
                  Export CSV
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Asset</TableHead>
                      <TableHead>Side</TableHead>
                      <TableHead className="text-right">Entry</TableHead>
                      <TableHead className="text-right">Exit</TableHead>
                      <TableHead className="text-right">P&L</TableHead>
                      <TableHead className="text-right">Return</TableHead>
                      <TableHead>Closed</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {state.closedTrades.slice(0, 20).map((trade) => (
                      <TableRow key={trade.id + trade.closedAt}>
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
                          ${trade.entryPrice.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </TableCell>
                        <TableCell className="text-right font-mono text-white text-xs">
                          ${trade.exitPrice.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </TableCell>
                        <TableCell
                          className={`text-right font-mono ${
                            trade.pnl >= 0 ? "text-green-400" : "text-red-400"
                          }`}
                        >
                          {trade.pnl >= 0 ? "+" : ""}${Math.abs(trade.pnl).toFixed(2)}
                        </TableCell>
                        <TableCell
                          className={`text-right font-mono text-xs ${
                            trade.pnlPercent >= 0 ? "text-green-400" : "text-red-400"
                          }`}
                        >
                          {trade.pnlPercent >= 0 ? "+" : ""}{trade.pnlPercent.toFixed(2)}%
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">
                          {new Date(trade.closedAt).toLocaleDateString("en-US", {
                            month: "short",
                            day: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </>
  );
}
