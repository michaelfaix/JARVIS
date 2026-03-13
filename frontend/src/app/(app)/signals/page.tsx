// =============================================================================
// src/app/(app)/signals/page.tsx — Live Signal Feed + Paper Trading
// =============================================================================

"use client";

import { useEffect, useMemo, useState } from "react";
import { HudPanel } from "@/components/ui/hud-panel";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { useSignals } from "@/hooks/use-signals";
import { useSystemStatus } from "@/hooks/use-jarvis";
import { usePortfolio } from "@/hooks/use-portfolio";
import { usePrices } from "@/hooks/use-prices";
import { useProfile } from "@/hooks/use-profile";
import { useOrders } from "@/hooks/use-orders";
import { useAutoSLTP } from "@/hooks/use-auto-sl-tp";
import type { Signal } from "@/lib/types";
import { DEFAULT_ASSETS, FREE_ASSETS, TIER_LIMITS } from "@/lib/constants";
import { useToast } from "@/components/ui/toast";
import { useSignalAlerts } from "@/hooks/use-signal-alerts";
import { useNotifications } from "@/hooks/use-notifications";
import { OrderDialog } from "@/components/trading/order-dialog";
import MultiTfAnalysis from "@/components/signals/multi-tf-analysis";
import { ApiOfflineBanner } from "@/components/ui/api-offline-banner";
import {
  AlertTriangle,
  Radio,
  RefreshCw,
  X,
  Wifi,
  WifiOff,
  Clock,
  Lock,
  ShoppingCart,
  ListOrdered,
} from "lucide-react";

export default function SignalsPage() {
  const { regime, error: statusError } = useSystemStatus(5000);
  const { state: portfolio, openPosition, closePosition } = usePortfolio();
  const { prices, priceHistory, binanceConnected, wsConnected } = usePrices(5000);
  const { signals: allSignals, loading, error, refresh } = useSignals(regime, 10000, prices, priceHistory);
  const { toast } = useToast();
  const { tier, isPro } = useProfile();
  const { checkSignals } = useSignalAlerts();
  const { push: pushNotification } = useNotifications();
  const limits = TIER_LIMITS[tier];

  // Order management
  const {
    pendingOrders,
    placeOrder,
    cancelOrder,
    checkOrders,
  } = useOrders(openPosition);

  // Auto SL/TP
  const { setSLTP, checkSLTP } = useAutoSLTP(
    portfolio.positions,
    closePosition,
    pushNotification
  );

  // Order dialog state
  const [orderDialogSignal, setOrderDialogSignal] = useState<Signal | null>(null);

  // Notify on high-confidence signals
  useEffect(() => {
    if (allSignals.length > 0) checkSignals(allSignals);
  }, [allSignals, checkSignals]);

  // Auto-check pending orders whenever prices update
  useEffect(() => {
    if (pendingOrders.length > 0 && Object.keys(prices).length > 0) {
      const filled = checkOrders(prices);
      for (const order of filled) {
        toast(
          "success",
          `${order.type.replace("_", "-")} order filled: ${order.direction} ${order.asset}`
        );
        // SL/TP for filled limit orders will be set via the order dialog flow
      }
    }
  }, [prices, pendingOrders.length, checkOrders, toast]);

  // Auto-check SL/TP for open positions
  useEffect(() => {
    if (portfolio.positions.length > 0 && Object.keys(prices).length > 0) {
      checkSLTP(prices);
    }
  }, [prices, portfolio.positions.length, checkSLTP]);

  // Filter signals by tier
  const signals = useMemo(
    () =>
      isPro
        ? allSignals
        : allSignals.filter((s) => FREE_ASSETS.includes(s.asset)),
    [allSignals, isPro]
  );

  // Set of assets that have open positions
  const openAssets = useMemo(
    () => new Set(portfolio.positions.map((p) => p.asset)),
    [portfolio.positions]
  );

  // Map position ID by asset for quick close
  const positionByAsset = useMemo(() => {
    const map: Record<string, string> = {};
    for (const p of portfolio.positions) {
      map[p.asset] = p.id;
    }
    return map;
  }, [portfolio.positions]);

  const activeLongs = signals.filter((s) => s.direction === "LONG").length;
  const activeShorts = signals.filter((s) => s.direction === "SHORT").length;
  const avgConfidence =
    signals.length > 0
      ? signals.reduce((sum, s) => sum + s.confidence, 0) / signals.length
      : 0;

  function handleTrade(signal: Signal) {
    setOrderDialogSignal(signal);
  }

  function handlePlaceOrder(order: Parameters<typeof placeOrder>[0]) {
    const placed = placeOrder(order);
    if (placed.status === "filled") {
      const livePrice = order.limitPrice ?? prices[order.asset] ?? 0;
      toast(
        "success",
        `Opened ${order.direction} ${order.asset} at $${livePrice.toLocaleString()}`
      );
      pushNotification(
        "trade",
        `${order.direction} ${order.asset} Opened`,
        `Entry $${livePrice.toLocaleString()} · Size ${order.size.toFixed(4)} · Capital $${order.capitalAllocated.toFixed(0)}`
      );
      // Set SL/TP for market orders
      if (order.stopLoss != null && order.takeProfit != null) {
        // Find the most recent position for this asset
        setTimeout(() => {
          const pos = portfolio.positions.find((p) => p.asset === order.asset);
          if (pos) {
            setSLTP(pos.id, pos.asset, pos.direction, order.stopLoss!, order.takeProfit!);
          }
        }, 100);
      }
    } else if (placed.status === "pending") {
      toast(
        "info",
        `${order.type.replace("_", "-")} order placed for ${order.asset}`
      );
    }
  }

  function handleClose(asset: string) {
    const posId = positionByAsset[asset];
    if (posId) {
      const pos = portfolio.positions.find((p) => p.id === posId);
      closePosition(posId);
      toast("info", `Closed ${asset} position`);
      if (pos) {
        const pnl = pos.direction === "LONG"
          ? (pos.currentPrice - pos.entryPrice) * pos.size
          : (pos.entryPrice - pos.currentPrice) * pos.size;
        pushNotification(
          "trade",
          `${asset} Position Closed`,
          `${pnl >= 0 ? "+" : ""}$${pnl.toFixed(2)} P&L · Entry $${pos.entryPrice.toLocaleString()} → Exit $${pos.currentPrice.toLocaleString()}`
        );
      }
    }
  }

  return (
    <>
      <div className="p-2 sm:p-3 md:p-4 space-y-3">
        {(error || statusError) && <ApiOfflineBanner />}

        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
            <div className="text-[10px] text-hud-cyan/70 font-mono mb-1">
              ACTIVE SIGNALS
            </div>
            <div className="text-2xl font-bold font-mono text-hud-cyan">
              {signals.length}
            </div>
          </div>
          <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
            <div className="text-[10px] text-hud-cyan/70 font-mono mb-1">
              LONG / SHORT
            </div>
            <div className="text-xl font-bold font-mono">
              <span className="text-hud-green">{activeLongs}</span>
              <span className="text-hud-border mx-1">/</span>
              <span className="text-hud-red">{activeShorts}</span>
            </div>
          </div>
          <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
            <div className="text-[10px] text-hud-cyan/70 font-mono mb-1">
              AVG CONFIDENCE
            </div>
            <div className="text-xl font-bold font-mono text-hud-cyan">
              {(avgConfidence * 100).toFixed(1)}%
            </div>
          </div>
          <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
            <div className="text-[10px] text-hud-cyan/70 font-mono mb-1">
              OPEN TRADES
            </div>
            <div className="text-xl font-bold font-mono text-hud-cyan">
              {portfolio.positions.length}
            </div>
          </div>
          <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
            <div className="text-[10px] text-hud-cyan/70 font-mono mb-1 flex items-center gap-1">
              {binanceConnected ? (
                <Wifi className="h-3 w-3 text-hud-green" />
              ) : (
                <WifiOff className="h-3 w-3 text-hud-amber" />
              )}
              PRICE FEED
            </div>
            <div className="text-sm font-mono">
              {wsConnected ? (
                <span className="text-hud-green">WS Live</span>
              ) : binanceConnected ? (
                <span className="text-hud-green">REST Live</span>
              ) : (
                <span className="text-hud-amber">Synthetic</span>
              )}
            </div>
          </div>
        </div>

        {/* Signal Feed Table */}
        <HudPanel title="SIGNAL FEED" scanLine>
          <div className="p-2.5">
            <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
              <div className="flex items-center gap-2">
                {loading && (
                  <RefreshCw className="h-3 w-3 animate-spin text-hud-cyan" />
                )}
                {!isPro && (
                  <Badge className="bg-hud-amber/15 text-hud-amber border-hud-amber/30 text-[10px] gap-1">
                    <Clock className="h-2.5 w-2.5" />
                    {limits.signalDelayMinutes}min delay
                  </Badge>
                )}
                {!isPro && allSignals.length > signals.length && (
                  <Badge className="bg-hud-cyan/15 text-hud-cyan border-hud-cyan/30 text-[10px] gap-1">
                    <Lock className="h-2.5 w-2.5" />
                    {signals.length}/{allSignals.length} assets
                  </Badge>
                )}
                {pendingOrders.length > 0 && (
                  <Badge className="bg-hud-amber/15 text-hud-amber border-hud-amber/30 text-[10px] gap-1">
                    <ListOrdered className="h-2.5 w-2.5" />
                    {pendingOrders.length} pending
                  </Badge>
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-hud-cyan/60 font-mono">
                  Available: $
                  {portfolio.availableCapital.toLocaleString("en-US", {
                    maximumFractionDigits: 0,
                  })}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={refresh}
                  className="h-7 text-xs bg-hud-cyan/15 text-hud-cyan border-hud-cyan/30 hover:bg-hud-cyan/25"
                >
                  <RefreshCw className="h-3 w-3 mr-1" />
                  Refresh
                </Button>
              </div>
            </div>

            {error && (
              <div className="mb-4 rounded bg-hud-red/10 border border-hud-red/20 p-3 text-sm text-hud-red font-mono">
                {error}. Backend may be offline.
              </div>
            )}

            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-hud-border/30">
                    <TableHead className="text-[10px] text-hud-cyan/70 font-mono">Asset</TableHead>
                    <TableHead className="text-[10px] text-hud-cyan/70 font-mono">Direction</TableHead>
                    <TableHead className="text-[10px] text-hud-cyan/70 font-mono text-right">Live Price</TableHead>
                    <TableHead className="text-[10px] text-hud-cyan/70 font-mono text-right">Stop Loss</TableHead>
                    <TableHead className="text-[10px] text-hud-cyan/70 font-mono text-right">Take Profit</TableHead>
                    <TableHead className="text-[10px] text-hud-cyan/70 font-mono">Confidence</TableHead>
                    <TableHead className="text-[10px] text-hud-cyan/70 font-mono text-right">Quality</TableHead>
                    <TableHead className="text-[10px] text-hud-cyan/70 font-mono">OOD</TableHead>
                    <TableHead className="text-[10px] text-hud-cyan/70 font-mono text-center">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {signals.length === 0 && !loading ? (
                    <TableRow className="border-hud-border/20">
                      <TableCell colSpan={9} className="py-12">
                        <div className="flex flex-col items-center justify-center gap-3 text-hud-cyan/50">
                          {error ? (
                            <>
                              <WifiOff className="h-8 w-8 text-hud-amber/60" />
                              <div className="text-sm font-medium font-mono text-hud-amber">
                                Unable to fetch signals
                              </div>
                              <div className="text-[10px] text-hud-cyan/40 font-mono">
                                Connect the JARVIS backend to generate live signals
                              </div>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={refresh}
                                className="mt-1 h-7 text-xs bg-hud-cyan/15 text-hud-cyan border-hud-cyan/30 hover:bg-hud-cyan/25"
                              >
                                <RefreshCw className="h-3 w-3 mr-1" />
                                Retry
                              </Button>
                            </>
                          ) : (
                            <>
                              <Radio className="h-8 w-8 text-hud-cyan/30" />
                              <div className="text-sm font-medium font-mono">
                                No signals available
                              </div>
                              <div className="text-[10px] font-mono">
                                Signals will appear here when the model generates predictions
                              </div>
                            </>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : (
                    signals.map((signal) => {
                      const asset = DEFAULT_ASSETS.find(
                        (a) => a.symbol === signal.asset
                      );
                      const livePrice = prices[signal.asset] ?? signal.entry;
                      const hasPosition = openAssets.has(signal.asset);

                      return (
                        <TableRow key={signal.id} className="border-hud-border/20">
                          <TableCell>
                            <div>
                              <div className="font-medium font-mono text-hud-cyan">
                                {signal.asset}
                              </div>
                              <div className="text-[10px] text-hud-cyan/50 font-mono">
                                {asset?.name}
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge
                              className={
                                signal.direction === "LONG"
                                  ? "bg-hud-green/15 text-hud-green border-hud-green/30"
                                  : "bg-hud-red/15 text-hud-red border-hud-red/30"
                              }
                            >
                              {signal.direction}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right font-mono text-hud-cyan">
                            $
                            {livePrice.toLocaleString("en-US", {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            })}
                          </TableCell>
                          <TableCell className="text-right font-mono text-hud-red text-xs">
                            $
                            {signal.stopLoss.toLocaleString("en-US", {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            })}
                          </TableCell>
                          <TableCell className="text-right font-mono text-hud-green text-xs">
                            $
                            {signal.takeProfit.toLocaleString("en-US", {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            })}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2 w-28">
                              <Progress
                                value={signal.confidence * 100}
                                className="h-1.5"
                                indicatorClassName={
                                  signal.confidence > 0.7
                                    ? "bg-hud-green"
                                    : signal.confidence > 0.4
                                    ? "bg-hud-amber"
                                    : "bg-hud-red"
                                }
                              />
                              <span className="text-xs font-mono text-hud-cyan/60 w-10 text-right">
                                {(signal.confidence * 100).toFixed(0)}%
                              </span>
                            </div>
                          </TableCell>
                          <TableCell className="text-right font-mono">
                            <span
                              className={
                                signal.qualityScore > 0.7
                                  ? "text-hud-green"
                                  : signal.qualityScore > 0.4
                                  ? "text-hud-amber"
                                  : "text-hud-red"
                              }
                            >
                              {(signal.qualityScore * 100).toFixed(0)}
                            </span>
                          </TableCell>
                          <TableCell>
                            {isPro ? (
                              signal.isOod ? (
                                <div className="flex items-center gap-1">
                                  <AlertTriangle className="h-4 w-4 text-hud-amber" />
                                  <span className="text-[10px] text-hud-amber font-mono">OOD</span>
                                </div>
                              ) : (
                                <span className="text-[10px] text-hud-green font-mono">OK</span>
                              )
                            ) : (
                              <Lock className="h-3 w-3 text-hud-cyan/40" />
                            )}
                          </TableCell>
                          <TableCell className="text-center">
                            {hasPosition ? (
                              <Button
                                variant="outline"
                                size="sm"
                                className="h-7 text-xs border-hud-red/30 text-hud-red hover:bg-hud-red/10 gap-1"
                                onClick={() => handleClose(signal.asset)}
                              >
                                <X className="h-3 w-3" />
                                Close
                              </Button>
                            ) : (
                              <Button
                                variant="outline"
                                size="sm"
                                className="h-7 text-xs bg-hud-cyan/15 text-hud-cyan border-hud-cyan/30 hover:bg-hud-cyan/25 gap-1"
                                onClick={() => handleTrade(signal)}
                                disabled={portfolio.availableCapital < 1}
                              >
                                <ShoppingCart className="h-3 w-3" />
                                Trade
                              </Button>
                            )}
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

        {/* Pending Orders Section */}
        {pendingOrders.length > 0 && (
          <HudPanel title={`PENDING ORDERS (${pendingOrders.length})`}>
            <div className="p-2.5">
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="border-hud-border/30">
                      <TableHead className="text-[10px] text-hud-cyan/70 font-mono">Asset</TableHead>
                      <TableHead className="text-[10px] text-hud-cyan/70 font-mono">Direction</TableHead>
                      <TableHead className="text-[10px] text-hud-cyan/70 font-mono">Type</TableHead>
                      <TableHead className="text-[10px] text-hud-cyan/70 font-mono text-right">Limit Price</TableHead>
                      <TableHead className="text-[10px] text-hud-cyan/70 font-mono text-right">Stop Price</TableHead>
                      <TableHead className="text-[10px] text-hud-cyan/70 font-mono text-right">Size</TableHead>
                      <TableHead className="text-[10px] text-hud-cyan/70 font-mono text-right">Capital</TableHead>
                      <TableHead className="text-[10px] text-hud-cyan/70 font-mono">Created</TableHead>
                      <TableHead className="text-[10px] text-hud-cyan/70 font-mono text-center">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pendingOrders.map((order) => (
                      <TableRow key={order.id} className="border-hud-border/20">
                        <TableCell className="font-medium font-mono text-hud-cyan">
                          {order.asset}
                        </TableCell>
                        <TableCell>
                          <Badge
                            className={
                              order.direction === "LONG"
                                ? "bg-hud-green/15 text-hud-green border-hud-green/30"
                                : "bg-hud-red/15 text-hud-red border-hud-red/30"
                            }
                          >
                            {order.direction}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge className="bg-hud-amber/15 text-hud-amber border-hud-amber/30 text-[10px]">
                            {order.type === "stop_limit" ? "Stop Limit" : "Limit"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right font-mono text-xs text-hud-cyan">
                          {order.limitPrice != null
                            ? `$${order.limitPrice.toLocaleString("en-US", {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2,
                              })}`
                            : "—"}
                        </TableCell>
                        <TableCell className="text-right font-mono text-xs text-hud-cyan/60">
                          {order.stopPrice != null
                            ? `$${order.stopPrice.toLocaleString("en-US", {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2,
                              })}`
                            : "—"}
                        </TableCell>
                        <TableCell className="text-right font-mono text-xs text-hud-cyan">
                          {order.size.toFixed(4)}
                        </TableCell>
                        <TableCell className="text-right font-mono text-xs text-hud-cyan/60">
                          ${order.capitalAllocated.toFixed(0)}
                        </TableCell>
                        <TableCell className="text-xs text-hud-cyan/60 font-mono">
                          {new Date(order.createdAt).toLocaleTimeString("en-US", {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </TableCell>
                        <TableCell className="text-center">
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-7 text-xs border-hud-red/30 text-hud-red hover:bg-hud-red/10 gap-1"
                            onClick={() => {
                              cancelOrder(order.id);
                              toast("warning", `Cancelled ${order.type} order for ${order.asset}`);
                            }}
                          >
                            <X className="h-3 w-3" />
                            Cancel
                          </Button>
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

      {/* Multi-Timeframe Analysis */}
      {signals.length > 0 && (
        <MultiTfAnalysis
          asset={signals[0].asset}
          currentPrice={prices[signals[0].asset] ?? signals[0].entry}
        />
      )}

      {/* Order Dialog */}
      {orderDialogSignal && (
        <OrderDialog
          signal={orderDialogSignal}
          currentPrice={prices[orderDialogSignal.asset] ?? orderDialogSignal.entry}
          availableCapital={portfolio.availableCapital}
          onPlaceOrder={handlePlaceOrder}
          onClose={() => setOrderDialogSignal(null)}
        />
      )}
    </>
  );
}
