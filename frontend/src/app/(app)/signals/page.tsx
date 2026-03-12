// =============================================================================
// src/app/(app)/signals/page.tsx — Live Signal Feed + Paper Trading
// =============================================================================

"use client";

import { useEffect, useMemo } from "react";
import { AppHeader } from "@/components/layout/app-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { inferRegime } from "@/lib/types";
import { DEFAULT_ASSETS, FREE_ASSETS, TIER_LIMITS } from "@/lib/constants";
import { useToast } from "@/components/ui/toast";
import { useSignalAlerts } from "@/hooks/use-signal-alerts";
import {
  AlertTriangle,
  Radio,
  RefreshCw,
  Check,
  X,
  Wifi,
  WifiOff,
  Clock,
  Lock,
} from "lucide-react";

const TRADE_CAPITAL_PERCENT = 0.1; // 10% of available capital per trade

export default function SignalsPage() {
  const { status } = useSystemStatus(5000);
  const regime = status ? inferRegime(status.modus) : "RISK_ON";
  const { signals: allSignals, loading, error, refresh } = useSignals(regime, 10000);
  const { state: portfolio, openPosition, closePosition } = usePortfolio();
  const { prices, binanceConnected, wsConnected } = usePrices(5000);
  const { toast } = useToast();
  const { tier, isPro } = useProfile();
  const { checkSignals } = useSignalAlerts();
  const limits = TIER_LIMITS[tier];

  // Notify on high-confidence signals
  useEffect(() => {
    if (allSignals.length > 0) checkSignals(allSignals);
  }, [allSignals, checkSignals]);

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

  function handleAccept(signal: (typeof signals)[number]) {
    const livePrice = prices[signal.asset] ?? signal.entry;
    const capitalForTrade = Math.min(
      portfolio.availableCapital * TRADE_CAPITAL_PERCENT,
      portfolio.availableCapital
    );
    if (capitalForTrade < 1) return;

    const size = capitalForTrade / livePrice;

    openPosition({
      asset: signal.asset,
      direction: signal.direction,
      entryPrice: livePrice,
      size,
      capitalAllocated: capitalForTrade,
      openedAt: new Date().toISOString(),
    });
    toast("success", `Opened ${signal.direction} ${signal.asset} at $${livePrice.toLocaleString()}`);
  }

  function handleClose(asset: string) {
    const posId = positionByAsset[asset];
    if (posId) {
      closePosition(posId);
      toast("info", `Closed ${asset} position`);
    }
  }

  return (
    <>
      <AppHeader title="Signals" subtitle="Live Signal Feed" />
      <div className="p-6 space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="text-xs text-muted-foreground mb-1">
                Active Signals
              </div>
              <div className="text-2xl font-bold font-mono text-white">
                {signals.length}
              </div>
            </CardContent>
          </Card>
          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="text-xs text-muted-foreground mb-1">
                Long / Short
              </div>
              <div className="text-xl font-bold font-mono">
                <span className="text-green-400">{activeLongs}</span>
                <span className="text-muted-foreground mx-1">/</span>
                <span className="text-red-400">{activeShorts}</span>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="text-xs text-muted-foreground mb-1">
                Avg Confidence
              </div>
              <div className="text-xl font-bold font-mono text-white">
                {(avgConfidence * 100).toFixed(1)}%
              </div>
            </CardContent>
          </Card>
          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="text-xs text-muted-foreground mb-1">
                Open Trades
              </div>
              <div className="text-xl font-bold font-mono text-blue-400">
                {portfolio.positions.length}
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
                {wsConnected ? (
                  <span className="text-green-400">WS Live</span>
                ) : binanceConnected ? (
                  <span className="text-green-400">REST Live</span>
                ) : (
                  <span className="text-yellow-400">Synthetic</span>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Signal Feed Table */}
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <Radio className="h-4 w-4" />
                Signal Feed
                {loading && (
                  <RefreshCw className="h-3 w-3 animate-spin text-blue-400" />
                )}
                {!isPro && (
                  <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30 text-[10px] gap-1">
                    <Clock className="h-2.5 w-2.5" />
                    {limits.signalDelayMinutes}min delay
                  </Badge>
                )}
                {!isPro && allSignals.length > signals.length && (
                  <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30 text-[10px] gap-1">
                    <Lock className="h-2.5 w-2.5" />
                    {signals.length}/{allSignals.length} assets
                  </Badge>
                )}
              </CardTitle>
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-muted-foreground">
                  Available: $
                  {portfolio.availableCapital.toLocaleString("en-US", {
                    maximumFractionDigits: 0,
                  })}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={refresh}
                  className="h-7 text-xs"
                >
                  <RefreshCw className="h-3 w-3 mr-1" />
                  Refresh
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {error && (
              <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">
                {error}. Backend may be offline.
              </div>
            )}

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Asset</TableHead>
                  <TableHead>Direction</TableHead>
                  <TableHead className="text-right">Live Price</TableHead>
                  <TableHead className="text-right">Stop Loss</TableHead>
                  <TableHead className="text-right">Take Profit</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead className="text-right">Quality</TableHead>
                  <TableHead>OOD</TableHead>
                  <TableHead className="text-center">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {signals.length === 0 && !loading ? (
                  <TableRow>
                    <TableCell
                      colSpan={9}
                      className="text-center text-muted-foreground py-8"
                    >
                      {error
                        ? "Connect backend to see signals"
                        : "No signals available"}
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
                      <TableRow key={signal.id}>
                        <TableCell>
                          <div>
                            <div className="font-medium text-white">
                              {signal.asset}
                            </div>
                            <div className="text-[10px] text-muted-foreground">
                              {asset?.name}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge
                            className={
                              signal.direction === "LONG"
                                ? "bg-green-500/20 text-green-400 border-green-500/30"
                                : "bg-red-500/20 text-red-400 border-red-500/30"
                            }
                          >
                            {signal.direction}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right font-mono text-white">
                          $
                          {livePrice.toLocaleString("en-US", {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </TableCell>
                        <TableCell className="text-right font-mono text-red-400 text-xs">
                          $
                          {signal.stopLoss.toLocaleString("en-US", {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </TableCell>
                        <TableCell className="text-right font-mono text-green-400 text-xs">
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
                                  ? "bg-green-500"
                                  : signal.confidence > 0.4
                                  ? "bg-yellow-500"
                                  : "bg-red-500"
                              }
                            />
                            <span className="text-xs font-mono text-muted-foreground w-10 text-right">
                              {(signal.confidence * 100).toFixed(0)}%
                            </span>
                          </div>
                        </TableCell>
                        <TableCell className="text-right font-mono">
                          <span
                            className={
                              signal.qualityScore > 0.7
                                ? "text-green-400"
                                : signal.qualityScore > 0.4
                                ? "text-yellow-400"
                                : "text-red-400"
                            }
                          >
                            {(signal.qualityScore * 100).toFixed(0)}
                          </span>
                        </TableCell>
                        <TableCell>
                          {isPro ? (
                            signal.isOod ? (
                              <div className="flex items-center gap-1">
                                <AlertTriangle className="h-4 w-4 text-yellow-500" />
                                <span className="text-[10px] text-yellow-400">OOD</span>
                              </div>
                            ) : (
                              <span className="text-[10px] text-green-400">OK</span>
                            )
                          ) : (
                            <Lock className="h-3 w-3 text-muted-foreground" />
                          )}
                        </TableCell>
                        <TableCell className="text-center">
                          {hasPosition ? (
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-7 text-xs border-red-500/30 text-red-400 hover:bg-red-500/10 gap-1"
                              onClick={() => handleClose(signal.asset)}
                            >
                              <X className="h-3 w-3" />
                              Close
                            </Button>
                          ) : (
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-7 text-xs border-green-500/30 text-green-400 hover:bg-green-500/10 gap-1"
                              onClick={() => handleAccept(signal)}
                              disabled={portfolio.availableCapital < 1}
                            >
                              <Check className="h-3 w-3" />
                              Accept
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
