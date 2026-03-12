// =============================================================================
// src/app/(app)/markets/page.tsx — Market Overview with Heatmap
// =============================================================================

"use client";

import { useEffect, useRef, useState } from "react";
import { AppHeader } from "@/components/layout/app-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { usePrices } from "@/hooks/use-prices";
import { useSignals } from "@/hooks/use-signals";
import { useSystemStatus } from "@/hooks/use-jarvis";
import { inferRegime, type RegimeState } from "@/lib/types";
import { DEFAULT_ASSETS } from "@/lib/constants";
import {
  LayoutGrid,
  TrendingUp,
  TrendingDown,
  Minus,
  Zap,
  Globe,
} from "lucide-react";

export default function MarketsPage() {
  const { prices, wsConnected, binanceConnected } = usePrices(5000);
  const { status } = useSystemStatus(5000);
  const regime: RegimeState = status ? inferRegime(status.modus) : "RISK_ON";
  const { signals } = useSignals(regime, 10000);

  // Track previous prices for change calculation
  const prevPricesRef = useRef<Record<string, number>>({});
  const [changes, setChanges] = useState<Record<string, number>>({});

  useEffect(() => {
    const prev = prevPricesRef.current;
    const newChanges: Record<string, number> = {};
    for (const asset of DEFAULT_ASSETS) {
      const current = prices[asset.symbol];
      const previous = prev[asset.symbol];
      if (current && previous) {
        newChanges[asset.symbol] = ((current - previous) / previous) * 100;
      } else {
        newChanges[asset.symbol] = 0;
      }
    }
    setChanges(newChanges);

    // Update prev with a delay so we see meaningful changes
    const timer = setTimeout(() => {
      prevPricesRef.current = { ...prices };
    }, 10000);
    return () => clearTimeout(timer);
  }, [prices]);

  // Initialize prev prices on first load
  useEffect(() => {
    if (Object.keys(prevPricesRef.current).length === 0) {
      prevPricesRef.current = { ...prices };
    }
  }, [prices]);

  const signalMap = new Map(signals.map((s) => [s.asset, s]));

  // Market stats
  const gainers = Object.entries(changes).filter(([, v]) => v > 0).length;
  const losers = Object.entries(changes).filter(([, v]) => v < 0).length;

  return (
    <>
      <AppHeader title="Markets" subtitle="Overview & Heatmap" />
      <div className="p-6 space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                <Globe className="h-3 w-3" /> Assets Tracked
              </div>
              <div className="text-2xl font-bold font-mono text-white">
                {DEFAULT_ASSETS.length}
              </div>
            </CardContent>
          </Card>
          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                <TrendingUp className="h-3 w-3 text-green-400" /> Gainers
              </div>
              <div className="text-2xl font-bold font-mono text-green-400">
                {gainers}
              </div>
            </CardContent>
          </Card>
          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                <TrendingDown className="h-3 w-3 text-red-400" /> Losers
              </div>
              <div className="text-2xl font-bold font-mono text-red-400">
                {losers}
              </div>
            </CardContent>
          </Card>
          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                <Zap className="h-3 w-3" /> Feed
              </div>
              <div className="text-sm font-mono text-white">
                {wsConnected ? (
                  <span className="text-green-400">WS Live</span>
                ) : binanceConnected ? (
                  <span className="text-green-400">REST</span>
                ) : (
                  <span className="text-yellow-400">Synthetic</span>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Heatmap */}
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <LayoutGrid className="h-4 w-4" />
              Market Heatmap
              <span className="text-[10px] text-muted-foreground ml-auto">
                Size = market cap weight · Color = price change
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {DEFAULT_ASSETS.map((asset) => {
                const price = prices[asset.symbol] ?? asset.price;
                const change = changes[asset.symbol] ?? 0;
                const signal = signalMap.get(asset.symbol);

                // Color intensity based on change magnitude
                const intensity = Math.min(Math.abs(change) * 20, 1);
                const bgColor =
                  change > 0
                    ? `rgba(34, 197, 94, ${0.05 + intensity * 0.2})`
                    : change < 0
                    ? `rgba(239, 68, 68, ${0.05 + intensity * 0.2})`
                    : "rgba(107, 114, 128, 0.05)";
                const borderColor =
                  change > 0
                    ? `rgba(34, 197, 94, ${0.15 + intensity * 0.3})`
                    : change < 0
                    ? `rgba(239, 68, 68, ${0.15 + intensity * 0.3})`
                    : "rgba(107, 114, 128, 0.15)";

                // Larger tiles for major assets
                const isLarge = ["BTC", "ETH", "SPY"].includes(asset.symbol);

                return (
                  <div
                    key={asset.symbol}
                    className={`rounded-lg border p-4 transition-colors ${
                      isLarge ? "md:col-span-1 row-span-1" : ""
                    }`}
                    style={{ backgroundColor: bgColor, borderColor }}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white text-lg">
                          {asset.symbol}
                        </span>
                        {signal && (
                          <Badge
                            className={`text-[8px] px-1 py-0 ${
                              signal.direction === "LONG"
                                ? "bg-green-500/20 text-green-400 border-green-500/30"
                                : "bg-red-500/20 text-red-400 border-red-500/30"
                            }`}
                          >
                            {signal.direction}
                          </Badge>
                        )}
                      </div>
                      {change > 0 ? (
                        <TrendingUp className="h-4 w-4 text-green-400" />
                      ) : change < 0 ? (
                        <TrendingDown className="h-4 w-4 text-red-400" />
                      ) : (
                        <Minus className="h-4 w-4 text-muted-foreground" />
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground mb-1">
                      {asset.name}
                    </div>
                    <div className="text-lg font-mono font-bold text-white">
                      $
                      {price.toLocaleString("en-US", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </div>
                    <div
                      className={`text-sm font-mono font-medium ${
                        change > 0
                          ? "text-green-400"
                          : change < 0
                          ? "text-red-400"
                          : "text-muted-foreground"
                      }`}
                    >
                      {change >= 0 ? "+" : ""}
                      {change.toFixed(3)}%
                    </div>
                    {signal && (
                      <div className="mt-2 text-[10px] text-muted-foreground">
                        Conf: {(signal.confidence * 100).toFixed(0)}% ·
                        Quality: {(signal.qualityScore * 100).toFixed(0)}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Asset Table */}
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              All Assets
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1">
              {DEFAULT_ASSETS.map((asset) => {
                const price = prices[asset.symbol] ?? asset.price;
                const change = changes[asset.symbol] ?? 0;
                const signal = signalMap.get(asset.symbol);

                return (
                  <div
                    key={asset.symbol}
                    className="flex items-center gap-4 rounded-lg bg-background/50 px-4 py-3"
                  >
                    <div className="w-16">
                      <span className="font-bold text-white">
                        {asset.symbol}
                      </span>
                    </div>
                    <div className="flex-1 text-xs text-muted-foreground">
                      {asset.name}
                    </div>
                    {signal && (
                      <Badge
                        className={`text-[9px] ${
                          signal.direction === "LONG"
                            ? "bg-green-500/20 text-green-400 border-green-500/30"
                            : "bg-red-500/20 text-red-400 border-red-500/30"
                        }`}
                      >
                        {signal.direction} {(signal.confidence * 100).toFixed(0)}%
                      </Badge>
                    )}
                    <div className="text-right w-28">
                      <div className="text-sm font-mono text-white">
                        $
                        {price.toLocaleString("en-US", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </div>
                    </div>
                    <div
                      className={`text-right w-20 text-sm font-mono ${
                        change > 0
                          ? "text-green-400"
                          : change < 0
                          ? "text-red-400"
                          : "text-muted-foreground"
                      }`}
                    >
                      {change >= 0 ? "+" : ""}
                      {change.toFixed(3)}%
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
