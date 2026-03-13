// =============================================================================
// src/app/(app)/markets/page.tsx — Market Overview with Heatmap
// =============================================================================

"use client";

import { useEffect, useRef, useState } from "react";
import { HudPanel } from "@/components/ui/hud-panel";
import { Badge } from "@/components/ui/badge";
import { usePrices } from "@/hooks/use-prices";
import { useSignals } from "@/hooks/use-signals";
import { useSystemStatus } from "@/hooks/use-jarvis";
import { DEFAULT_ASSETS } from "@/lib/constants";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Zap,
  Globe,
} from "lucide-react";
import { ApiOfflineBanner } from "@/components/ui/api-offline-banner";

export default function MarketsPage() {
  const { prices, priceHistory, wsConnected, binanceConnected } = usePrices(5000);
  const { regime, error: statusError } = useSystemStatus(5000);
  const { signals, error: signalsError } = useSignals(regime, 10000, prices, priceHistory);

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
      <div className="p-2 sm:p-3 md:p-4 space-y-3">
        {(statusError || signalsError) && <ApiOfflineBanner />}
        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
            <div className="flex items-center gap-2 text-[10px] text-hud-cyan/70 font-mono mb-1">
              <Globe className="h-3 w-3" /> ASSETS TRACKED
            </div>
            <div className="text-2xl font-bold font-mono text-hud-cyan">
              {DEFAULT_ASSETS.length}
            </div>
          </div>
          <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
            <div className="flex items-center gap-2 text-[10px] text-hud-cyan/70 font-mono mb-1">
              <TrendingUp className="h-3 w-3 text-hud-green" /> GAINERS
            </div>
            <div className="text-2xl font-bold font-mono text-hud-green">
              {gainers}
            </div>
          </div>
          <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
            <div className="flex items-center gap-2 text-[10px] text-hud-cyan/70 font-mono mb-1">
              <TrendingDown className="h-3 w-3 text-hud-red" /> LOSERS
            </div>
            <div className="text-2xl font-bold font-mono text-hud-red">
              {losers}
            </div>
          </div>
          <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
            <div className="flex items-center gap-2 text-[10px] text-hud-cyan/70 font-mono mb-1">
              <Zap className="h-3 w-3" /> FEED
            </div>
            <div className="text-sm font-mono">
              {wsConnected ? (
                <span className="text-hud-green">WS Live</span>
              ) : binanceConnected ? (
                <span className="text-hud-green">REST</span>
              ) : (
                <span className="text-hud-amber">Synthetic</span>
              )}
            </div>
          </div>
        </div>

        {/* Heatmap */}
        <HudPanel title="MARKET HEATMAP" scanLine>
          <div className="p-2.5">
            <div className="flex items-center justify-end mb-2">
              <span className="text-[9px] text-hud-cyan/40 font-mono">
                Size = market cap weight · Color = price change
              </span>
            </div>
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
                    className={`rounded border p-3 transition-colors ${
                      isLarge ? "md:col-span-1 row-span-1" : ""
                    }`}
                    style={{ backgroundColor: bgColor, borderColor }}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-bold font-mono text-hud-cyan text-lg">
                          {asset.symbol}
                        </span>
                        {signal && (
                          <Badge
                            className={`text-[8px] px-1 py-0 ${
                              signal.direction === "LONG"
                                ? "bg-hud-green/15 text-hud-green border-hud-green/30"
                                : "bg-hud-red/15 text-hud-red border-hud-red/30"
                            }`}
                          >
                            {signal.direction}
                          </Badge>
                        )}
                      </div>
                      {change > 0 ? (
                        <TrendingUp className="h-4 w-4 text-hud-green" />
                      ) : change < 0 ? (
                        <TrendingDown className="h-4 w-4 text-hud-red" />
                      ) : (
                        <Minus className="h-4 w-4 text-hud-cyan/40" />
                      )}
                    </div>
                    <div className="text-[10px] text-hud-cyan/50 font-mono mb-1">
                      {asset.name}
                    </div>
                    <div className="text-lg font-mono font-bold text-hud-cyan">
                      $
                      {price.toLocaleString("en-US", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </div>
                    <div
                      className={`text-sm font-mono font-medium ${
                        change > 0
                          ? "text-hud-green"
                          : change < 0
                          ? "text-hud-red"
                          : "text-hud-cyan/40"
                      }`}
                    >
                      {change >= 0 ? "+" : ""}
                      {change.toFixed(3)}%
                    </div>
                    {signal && (
                      <div className="mt-2 text-[10px] text-hud-cyan/50 font-mono">
                        Conf: {(signal.confidence * 100).toFixed(0)}% ·
                        Quality: {(signal.qualityScore * 100).toFixed(0)}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </HudPanel>

        {/* Asset Table */}
        <HudPanel title="ALL ASSETS">
          <div className="p-2.5">
            <div className="space-y-1">
              {DEFAULT_ASSETS.map((asset) => {
                const price = prices[asset.symbol] ?? asset.price;
                const change = changes[asset.symbol] ?? 0;
                const signal = signalMap.get(asset.symbol);

                return (
                  <div
                    key={asset.symbol}
                    className="flex items-center gap-4 rounded bg-hud-bg/60 border border-hud-border/20 px-4 py-3"
                  >
                    <div className="w-16">
                      <span className="font-bold font-mono text-hud-cyan">
                        {asset.symbol}
                      </span>
                    </div>
                    <div className="flex-1 text-[10px] text-hud-cyan/50 font-mono">
                      {asset.name}
                    </div>
                    {signal && (
                      <Badge
                        className={`text-[9px] ${
                          signal.direction === "LONG"
                            ? "bg-hud-green/15 text-hud-green border-hud-green/30"
                            : "bg-hud-red/15 text-hud-red border-hud-red/30"
                        }`}
                      >
                        {signal.direction} {(signal.confidence * 100).toFixed(0)}%
                      </Badge>
                    )}
                    <div className="text-right w-28">
                      <div className="text-sm font-mono text-hud-cyan">
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
                          ? "text-hud-green"
                          : change < 0
                          ? "text-hud-red"
                          : "text-hud-cyan/40"
                      }`}
                    >
                      {change >= 0 ? "+" : ""}
                      {change.toFixed(3)}%
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </HudPanel>
      </div>
    </>
  );
}
