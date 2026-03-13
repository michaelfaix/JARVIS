// =============================================================================
// src/app/(app)/portfolio/page.tsx — Paper Trading Portfolio
// =============================================================================

"use client";

import React, { useEffect } from "react";
import { HudPanel } from "@/components/ui/hud-panel";
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
import { useAutoSLTP } from "@/hooks/use-auto-sl-tp";
import { REGIME_COLORS } from "@/lib/types";
import { useToast } from "@/components/ui/toast";
import { EquityCurve } from "@/components/chart/equity-curve";
import { AnalyticsPanel } from "@/components/portfolio/analytics-panel";
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
  Star,
  X,
  Download,
  Zap,
  FileText,
} from "lucide-react";
import { PerformanceReport } from "@/components/portfolio/performance-report";
import GoalTracker from "@/components/portfolio/goal-tracker";
import { ApiOfflineBanner } from "@/components/ui/api-offline-banner";

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
  const { status, regime, error: statusError } = useSystemStatus(5000);
  const { prices, binanceConnected } = usePrices(5000);
  const { toast } = useToast();
  const { push: pushNotification } = useNotifications();

  // Auto SL/TP
  const { sltpMap, autoCloseHistory, checkSLTP } = useAutoSLTP(
    state.positions,
    closePosition,
    pushNotification
  );

  const [showReport, setShowReport] = React.useState(false);
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

  // Auto-check SL/TP for open positions
  useEffect(() => {
    if (state.positions.length > 0 && Object.keys(prices).length > 0) {
      checkSLTP(prices);
    }
  }, [prices, state.positions.length, checkSLTP]);

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

  // Last 5 auto-close events
  const recentAutoCloses = autoCloseHistory.slice(0, 5);

  return (
    <>
      <div className="px-2 sm:px-3 md:px-4 pt-3">
        {statusError && <ApiOfflineBanner />}
      </div>

      {/* Performance Report Modal */}
      {showReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="relative max-h-[90vh] overflow-y-auto rounded-xl">
            <div className="sticky top-0 z-10 flex items-center justify-end gap-2 p-2">
              <span className="text-[10px] text-muted-foreground/60 mr-auto pl-2">
                Screenshot this report to share
              </span>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-xs text-muted-foreground hover:text-white"
                onClick={() => setShowReport(false)}
              >
                <X className="h-3.5 w-3.5 mr-1" />
                Close
              </Button>
            </div>
            <PerformanceReport
              closedTrades={state.closedTrades}
              totalCapital={state.totalCapital}
              totalValue={totalValue}
              winRate={winRate}
            />
          </div>
        </div>
      )}

      <div className="p-2 sm:p-3 md:p-4 space-y-3">
        {/* Top Actions */}
        {state.closedTrades.length > 0 && (
          <div className="flex justify-end">
            <Button
              variant="outline"
              size="sm"
              className="h-8 text-xs gap-1.5 border-hud-border/50 text-hud-cyan hover:bg-hud-cyan/10"
              onClick={() => setShowReport(true)}
            >
              <FileText className="h-3.5 w-3.5" />
              Performance Report
            </Button>
          </div>
        )}

        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
            <div className="flex items-center gap-2 text-[10px] text-muted-foreground mb-1">
              <Wallet className="h-3 w-3" /> TOTAL VALUE
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              $
              {totalValue.toLocaleString("en-US", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </div>
          </div>

          <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
            <div className="flex items-center gap-2 text-[10px] text-muted-foreground mb-1">
              {totalPnl >= 0 ? (
                <TrendingUp className="h-3 w-3" />
              ) : (
                <TrendingDown className="h-3 w-3" />
              )}
              TOTAL P&L
            </div>
            <div
              className={`text-2xl font-bold font-mono ${
                totalPnl >= 0 ? "text-hud-green" : "text-hud-red"
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
                totalPnlPercent >= 0 ? "text-hud-green" : "text-hud-red"
              }`}
            >
              {totalPnlPercent >= 0 ? "+" : ""}
              {totalPnlPercent.toFixed(2)}%
            </div>
          </div>

          <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
            <div className="flex items-center gap-2 text-[10px] text-muted-foreground mb-1">
              <ShieldAlert className="h-3 w-3" /> RISK SCORE
            </div>
            <div
              className={`text-2xl font-bold font-mono ${
                riskScore < 30
                  ? "text-hud-green"
                  : riskScore < 60
                  ? "text-hud-amber"
                  : "text-hud-red"
              }`}
            >
              {riskScore}
            </div>
            <div className="text-[10px] text-muted-foreground font-mono">
              {riskScore < 30
                ? "Low Risk"
                : riskScore < 60
                ? "Moderate"
                : "High Risk"}
            </div>
          </div>

          <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
            <div className="text-[10px] text-muted-foreground mb-1">
              AVAILABLE CAPITAL
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              $
              {state.availableCapital.toLocaleString("en-US", {
                minimumFractionDigits: 0,
              })}
            </div>
            <div className="text-[10px] text-muted-foreground font-mono">
              of ${state.totalCapital.toLocaleString()}
            </div>
          </div>

          <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
            <div className="text-[10px] text-muted-foreground mb-1 flex items-center gap-1">
              {binanceConnected ? (
                <Wifi className="h-3 w-3 text-hud-green" />
              ) : (
                <WifiOff className="h-3 w-3 text-hud-amber" />
              )}
              PRICE FEED
            </div>
            <div className="text-sm font-mono text-white">
              {binanceConnected ? (
                <span className="text-hud-green">Binance Live</span>
              ) : (
                <span className="text-hud-amber">Synthetic</span>
              )}
            </div>
            <div className="text-[9px] text-muted-foreground font-mono">
              Updates every 5s
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
          {/* Asset Allocation */}
          <HudPanel title="ASSET ALLOCATION">
            <div className="p-2.5">
              <div className="space-y-3">
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
                          <span className="text-white font-medium font-mono">{asset}</span>
                          <span className="font-mono text-muted-foreground">
                            {pct.toFixed(1)}%
                          </span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-hud-bg/60 overflow-hidden">
                          <div
                            className="h-full rounded-full bg-hud-cyan"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })
                )}
                <Separator className="opacity-50 border-hud-border/30" />
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
              </div>
            </div>
          </HudPanel>

          {/* Open Positions Table */}
          <HudPanel title="OPEN POSITIONS" className="lg:col-span-2">
            <div className="p-2.5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] text-muted-foreground font-mono">
                  {state.positions.length} POSITIONS
                </span>
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
                      className="text-xs text-muted-foreground h-7 hover:text-hud-red"
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
              <div className="overflow-x-auto">
                <Table className="border-hud-border/30">
                  <TableHeader>
                    <TableRow className="border-hud-border/30">
                      <TableHead className="text-[10px] font-mono">Asset</TableHead>
                      <TableHead className="text-[10px] font-mono">Side</TableHead>
                      <TableHead className="text-right text-[10px] font-mono">Size</TableHead>
                      <TableHead className="text-right text-[10px] font-mono">Entry</TableHead>
                      <TableHead className="text-right text-[10px] font-mono">Current</TableHead>
                      <TableHead className="text-right text-[10px] font-mono">SL / TP</TableHead>
                      <TableHead className="text-right text-[10px] font-mono">P&L</TableHead>
                      <TableHead></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {state.positions.length === 0 ? (
                      <TableRow>
                        <TableCell
                          colSpan={8}
                          className="text-center text-muted-foreground py-8"
                        >
                          No open positions. Accept signals to open trades.
                        </TableCell>
                      </TableRow>
                    ) : (
                      state.positions.map((pos) => {
                        const sltp = sltpMap[pos.id];
                        return (
                          <TableRow key={pos.id} className="border-hud-border/30">
                            <TableCell className="font-medium text-white font-mono">
                              {pos.asset}
                            </TableCell>
                            <TableCell>
                              <Badge
                                className={
                                  pos.direction === "LONG"
                                    ? "bg-hud-green/20 text-hud-green border-hud-green/30"
                                    : "bg-hud-red/20 text-hud-red border-hud-red/30"
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
                            <TableCell className="text-right">
                              {sltp ? (
                                <div className="space-y-0.5">
                                  <div className="flex items-center justify-end gap-1">
                                    <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/30 text-[9px] px-1 py-0 gap-0.5">
                                      <Zap className="h-2 w-2" />
                                      Auto
                                    </Badge>
                                  </div>
                                  <div className="text-[10px] font-mono text-hud-red">
                                    SL: ${sltp.stopLoss.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                  </div>
                                  <div className="text-[10px] font-mono text-hud-green">
                                    TP: ${sltp.takeProfit.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                  </div>
                                </div>
                              ) : (
                                <span className="text-[10px] text-muted-foreground">—</span>
                              )}
                            </TableCell>
                            <TableCell
                              className={`text-right font-mono ${
                                pos.pnl >= 0 ? "text-hud-green" : "text-hud-red"
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
                                className="h-7 w-7 p-0 text-muted-foreground hover:text-hud-red"
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
                        );
                      })
                    )}
                  </TableBody>
                </Table>
              </div>
            </div>
          </HudPanel>
        </div>

        {/* Auto-Close History */}
        {recentAutoCloses.length > 0 && (
          <HudPanel title="AUTO-CLOSE HISTORY">
            <div className="p-2.5">
              <div className="flex items-center gap-2 mb-3">
                <Zap className="h-4 w-4 text-purple-400" />
                <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/30 text-[10px]">
                  SL/TP
                </Badge>
              </div>
              <div className="space-y-2">
                {recentAutoCloses.map((event) => (
                  <div
                    key={event.id}
                    className={`flex items-center justify-between rounded-lg border p-3 ${
                      event.reason === "stop_loss"
                        ? "border-hud-red/20 bg-hud-red/5"
                        : "border-hud-green/20 bg-hud-green/5"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Badge
                        className={
                          event.reason === "stop_loss"
                            ? "bg-hud-red/20 text-hud-red border-hud-red/30 text-[10px]"
                            : "bg-hud-green/20 text-hud-green border-hud-green/30 text-[10px]"
                        }
                      >
                        {event.reason === "stop_loss" ? "Stop Loss" : "Take Profit"}
                      </Badge>
                      <div>
                        <span className="text-sm font-medium text-white font-mono">
                          {event.asset}
                        </span>
                        <span className="text-xs text-muted-foreground ml-2 font-mono">
                          {event.direction}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-xs font-mono text-white">
                        ${event.triggerPrice.toLocaleString("en-US", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </span>
                      <span className="text-[10px] text-muted-foreground font-mono">
                        {new Date(event.timestamp).toLocaleString("en-US", {
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </HudPanel>
        )}

        {/* Trade Stats */}
        {state.closedTrades.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
              <div className="flex items-center gap-2 text-[10px] text-muted-foreground mb-1">
                <Trophy className="h-3 w-3" /> WIN RATE
              </div>
              <div className={`text-xl font-bold font-mono ${winRate >= 50 ? "text-hud-green" : "text-hud-red"}`}>
                {winRate.toFixed(1)}%
              </div>
            </div>
            <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
              <div className="text-[10px] text-muted-foreground mb-1">TOTAL TRADES</div>
              <div className="text-xl font-bold font-mono text-white">
                {state.closedTrades.length}
              </div>
            </div>
            <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
              <div className="text-[10px] text-muted-foreground mb-1">AVG WIN</div>
              <div className="text-xl font-bold font-mono text-hud-green">
                +${avgWin.toFixed(0)}
              </div>
            </div>
            <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
              <div className="text-[10px] text-muted-foreground mb-1">AVG LOSS</div>
              <div className="text-xl font-bold font-mono text-hud-red">
                ${avgLoss.toFixed(0)}
              </div>
            </div>
            <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
              <div className="flex items-center gap-2 text-[10px] text-muted-foreground mb-1">
                <BarChart3 className="h-3 w-3" /> DRAWDOWN
              </div>
              <div className={`text-xl font-bold font-mono ${drawdown > 5 ? "text-hud-red" : drawdown > 0 ? "text-hud-amber" : "text-hud-green"}`}>
                {drawdown.toFixed(2)}%
              </div>
            </div>
          </div>
        )}

        {/* Equity Curve */}
        {state.closedTrades.length >= 2 && (
          <HudPanel title="EQUITY CURVE" scanLine>
            <div className="p-2.5">
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
            </div>
          </HudPanel>
        )}

        {/* Portfolio Analytics */}
        {state.closedTrades.length >= 3 && (
          <AnalyticsPanel
            closedTrades={state.closedTrades}
            totalCapital={state.totalCapital}
          />
        )}

        {/* Achievements */}
        {state.closedTrades.length > 0 && (
          <HudPanel title="ACHIEVEMENTS">
            <div className="p-2.5">
              <div className="flex items-center gap-2 mb-3">
                <Star className="h-4 w-4 text-hud-amber" />
                <Badge variant="outline" className="ml-auto text-[10px] border-hud-border/30 text-hud-cyan">
                  {unlockedCount}/{achievements.length} unlocked
                </Badge>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {achievements.map((ach) => {
                  const tierColor =
                    ach.tier === "gold"
                      ? "border-hud-amber/30 bg-hud-amber/5"
                      : ach.tier === "silver"
                      ? "border-gray-400/30 bg-gray-400/5"
                      : "border-amber-700/30 bg-amber-700/5";

                  return (
                    <div
                      key={ach.id}
                      className={`rounded-lg border p-3 ${
                        ach.unlocked
                          ? tierColor
                          : "border-hud-border/30 bg-hud-bg/30 opacity-60"
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className="text-lg">{ach.icon}</span>
                        <span className="text-xs font-medium text-white truncate font-mono">
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
                              ? "bg-hud-amber"
                              : ach.tier === "silver"
                              ? "bg-gray-400"
                              : "bg-amber-700"
                            : "bg-muted-foreground/50"
                        }
                      />
                      {ach.unlocked && (
                        <div className="text-[9px] text-hud-green mt-1 font-mono">
                          Unlocked
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </HudPanel>
        )}

        {/* Portfolio Goals */}
        <GoalTracker
          currentValue={totalValue}
          startingCapital={state.totalCapital}
        />

        {/* Trade History */}
        {state.closedTrades.length > 0 && (
          <HudPanel title="TRADE JOURNAL">
            <div className="p-2.5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] text-muted-foreground font-mono">
                  {state.closedTrades.length} TRADES
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 text-xs gap-1 border-hud-border/50 text-hud-cyan hover:bg-hud-cyan/10"
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
              <div className="overflow-x-auto">
                <Table className="border-hud-border/30">
                  <TableHeader>
                    <TableRow className="border-hud-border/30">
                      <TableHead className="text-[10px] font-mono">Asset</TableHead>
                      <TableHead className="text-[10px] font-mono">Side</TableHead>
                      <TableHead className="text-right text-[10px] font-mono">Entry</TableHead>
                      <TableHead className="text-right text-[10px] font-mono">Exit</TableHead>
                      <TableHead className="text-right text-[10px] font-mono">P&L</TableHead>
                      <TableHead className="text-right text-[10px] font-mono">Return</TableHead>
                      <TableHead className="text-[10px] font-mono">Closed</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {state.closedTrades.slice(0, 20).map((trade) => (
                      <TableRow key={trade.id + trade.closedAt} className="border-hud-border/30">
                        <TableCell className="font-medium text-white font-mono">
                          {trade.asset}
                        </TableCell>
                        <TableCell>
                          <Badge
                            className={
                              trade.direction === "LONG"
                                ? "bg-hud-green/20 text-hud-green border-hud-green/30"
                                : "bg-hud-red/20 text-hud-red border-hud-red/30"
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
                            trade.pnl >= 0 ? "text-hud-green" : "text-hud-red"
                          }`}
                        >
                          {trade.pnl >= 0 ? "+" : ""}${Math.abs(trade.pnl).toFixed(2)}
                        </TableCell>
                        <TableCell
                          className={`text-right font-mono text-xs ${
                            trade.pnlPercent >= 0 ? "text-hud-green" : "text-hud-red"
                          }`}
                        >
                          {trade.pnlPercent >= 0 ? "+" : ""}{trade.pnlPercent.toFixed(2)}%
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground font-mono">
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
            </div>
          </HudPanel>
        )}
      </div>
    </>
  );
}
