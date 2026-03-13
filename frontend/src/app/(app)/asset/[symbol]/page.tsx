"use client";

import Link from "next/link";
import { useMemo } from "react";
import {
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  Target,
  Activity,
} from "lucide-react";
import { HudPanel } from "@/components/ui/hud-panel";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { AssetChart } from "@/components/chart/asset-chart";
import { DEFAULT_ASSETS } from "@/lib/constants";
import { usePrices } from "@/hooks/use-prices";
import { useSignals } from "@/hooks/use-signals";
import { usePortfolio } from "@/hooks/use-portfolio";
import { cn } from "@/lib/utils";
import { ApiOfflineBanner } from "@/components/ui/api-offline-banner";

// Binance symbol mapping — matches use-prices.ts
const BINANCE_SYMBOLS: Record<string, boolean> = {
  BTC: true,
  ETH: true,
  SOL: true,
};

function formatCurrency(value: number, decimals = 2): string {
  return value.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export default function AssetDetailPage({
  params,
}: {
  params: { symbol: string };
}) {
  const symbol = params.symbol.toUpperCase();
  const asset = DEFAULT_ASSETS.find((a) => a.symbol === symbol);

  const { prices, priceHistory, wsConnected, binanceConnected } = usePrices();
  const { signals, loading: signalsLoading, error: signalsError } = useSignals(undefined, undefined, prices, priceHistory);
  const { state: portfolioState } = usePortfolio();

  const assetIndex = useMemo(
    () => DEFAULT_ASSETS.findIndex((a) => a.symbol === symbol),
    [symbol]
  );

  const signal = useMemo(
    () => signals.find((s) => s.asset === symbol) ?? null,
    [signals, symbol]
  );

  const position = useMemo(
    () => portfolioState.positions.find((p) => p.asset === symbol) ?? null,
    [portfolioState.positions, symbol]
  );

  const relatedAssets = useMemo(
    () => DEFAULT_ASSETS.filter((a) => a.symbol !== symbol),
    [symbol]
  );

  // ---------- Asset not found ----------
  if (!asset || assetIndex === -1) {
    return (
      <div className="p-2 sm:p-3 md:p-4 space-y-3">
        <div className="flex flex-1 items-center justify-center">
          <HudPanel title="ASSET NOT FOUND" className="max-w-md w-full">
            <div className="p-8 text-center">
              <p className="text-muted-foreground mb-4">
                Asset &quot;{params.symbol}&quot; not found in tracked assets.
              </p>
              <Link
                href="/charts"
                className="inline-flex items-center gap-2 text-sm text-hud-cyan hover:text-hud-cyan/80 transition-colors"
              >
                <ArrowLeft className="h-4 w-4" />
                Back to All Assets
              </Link>
            </div>
          </HudPanel>
        </div>
      </div>
    );
  }

  // ---------- Derived values ----------
  const currentPrice = prices[symbol] ?? asset.price;
  const priceChange24h =
    ((currentPrice - asset.price) / asset.price) * 100;
  const isPositive = priceChange24h >= 0;

  const isCrypto = symbol in BINANCE_SYMBOLS;
  const feedStatus = isCrypto
    ? wsConnected
      ? "WS Live"
      : binanceConnected
        ? "REST"
        : "Synthetic"
    : "Synthetic";

  // ---------- Render ----------
  return (
    <div className="p-2 sm:p-3 md:p-4 space-y-3">
      {signalsError && <ApiOfflineBanner />}
      {/* ---------------------------------------------------------------- */}
      {/* 1. Header */}
      {/* ---------------------------------------------------------------- */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-4">
          <Link
            href="/charts"
            className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-white transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            <span className="hidden sm:inline">All Assets</span>
          </Link>

          <div className="flex items-baseline gap-3">
            <h2 className="text-2xl font-bold text-white">{asset.name}</h2>
            <span className="text-sm text-muted-foreground">{symbol}</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-2xl md:text-3xl font-mono font-bold text-white">
            ${formatCurrency(currentPrice)}
          </span>
          <Badge
            className={cn(
              "text-xs font-mono",
              isPositive
                ? "bg-hud-green/15 text-hud-green border-hud-green/30"
                : "bg-hud-red/15 text-hud-red border-hud-red/30"
            )}
          >
            {isPositive ? (
              <TrendingUp className="h-3 w-3 mr-1" />
            ) : (
              <TrendingDown className="h-3 w-3 mr-1" />
            )}
            {isPositive ? "+" : ""}
            {priceChange24h.toFixed(2)}%
          </Badge>
        </div>
      </div>

      {/* ---------------------------------------------------------------- */}
      {/* 2. Price Chart — full width */}
      {/* ---------------------------------------------------------------- */}
      <HudPanel title="PRICE CHART">
        <div className="p-4">
          <AssetChart
            symbol={symbol}
            name={asset.name}
            basePrice={asset.price}
            livePrice={currentPrice}
            height={400}
            interval="1h"
          />
        </div>
      </HudPanel>

      {/* ---------------------------------------------------------------- */}
      {/* 3 & 4: Signal Card + Position Card — side by side on desktop */}
      {/* ---------------------------------------------------------------- */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {/* --- Signal Card --- */}
        <HudPanel title="JARVIS SIGNAL">
          <div className="p-4">
            {signalsLoading ? (
              <p className="text-sm text-muted-foreground">
                Loading signals...
              </p>
            ) : signal ? (
              <div className="space-y-4">
                {/* Direction badge */}
                <div className="flex items-center gap-3">
                  <Badge
                    className={cn(
                      "text-sm px-3 py-1",
                      signal.direction === "LONG"
                        ? "bg-hud-green/15 text-hud-green border-hud-green/30"
                        : "bg-hud-red/15 text-hud-red border-hud-red/30"
                    )}
                  >
                    {signal.direction === "LONG" ? (
                      <TrendingUp className="h-3.5 w-3.5 mr-1.5" />
                    ) : (
                      <TrendingDown className="h-3.5 w-3.5 mr-1.5" />
                    )}
                    {signal.direction}
                  </Badge>
                  {signal.isOod && (
                    <Badge
                      variant="outline"
                      className="text-[10px] text-yellow-400 border-yellow-400/30"
                    >
                      OOD
                    </Badge>
                  )}
                </div>

                {/* Price levels */}
                <div className="grid grid-cols-3 gap-3 text-sm">
                  <div>
                    <p className="text-muted-foreground text-xs mb-1">
                      Entry
                    </p>
                    <p className="font-mono text-white">
                      ${formatCurrency(signal.entry)}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs mb-1">
                      Stop Loss
                    </p>
                    <p className="font-mono text-hud-red">
                      ${formatCurrency(signal.stopLoss)}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs mb-1">
                      Take Profit
                    </p>
                    <p className="font-mono text-hud-green">
                      ${formatCurrency(signal.takeProfit)}
                    </p>
                  </div>
                </div>

                {/* Confidence bar */}
                <div>
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <span className="text-muted-foreground">Confidence</span>
                    <span className="font-mono text-white">
                      {(signal.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <Progress
                    value={signal.confidence * 100}
                    className="h-2"
                    indicatorClassName={cn(
                      signal.confidence >= 0.7
                        ? "bg-hud-green"
                        : signal.confidence >= 0.4
                          ? "bg-yellow-500"
                          : "bg-hud-red"
                    )}
                  />
                </div>

                {/* Quality score */}
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Quality Score</span>
                  <span className="font-mono text-white">
                    {signal.qualityScore.toFixed(2)}
                  </span>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center py-6 text-muted-foreground">
                <Target className="h-8 w-8 mb-2 opacity-40" />
                <p className="text-sm">No active signal</p>
              </div>
            )}
          </div>
        </HudPanel>

        {/* --- Position Card --- */}
        <HudPanel title="OPEN POSITION">
          <div className="p-4">
            {position ? (
              <div className="space-y-4">
                {/* Direction */}
                <Badge
                  className={cn(
                    "text-sm px-3 py-1",
                    position.direction === "LONG"
                      ? "bg-hud-green/15 text-hud-green border-hud-green/30"
                      : "bg-hud-red/15 text-hud-red border-hud-red/30"
                  )}
                >
                  {position.direction}
                </Badge>

                {/* Position details */}
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-muted-foreground text-xs mb-1">
                      Entry Price
                    </p>
                    <p className="font-mono text-white">
                      ${formatCurrency(position.entryPrice)}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs mb-1">
                      Current Price
                    </p>
                    <p className="font-mono text-white">
                      ${formatCurrency(position.currentPrice)}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs mb-1">
                      Position Size
                    </p>
                    <p className="font-mono text-white">
                      {position.size.toLocaleString("en-US")}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs mb-1">
                      Allocated
                    </p>
                    <p className="font-mono text-white">
                      ${formatCurrency(position.capitalAllocated)}
                    </p>
                  </div>
                </div>

                {/* P&L */}
                <div
                  className={cn(
                    "rounded-lg p-3",
                    position.pnl >= 0 ? "bg-hud-green/10" : "bg-hud-red/10"
                  )}
                >
                  <p className="text-xs text-muted-foreground mb-1">
                    Unrealized P&L
                  </p>
                  <div className="flex items-baseline gap-2">
                    <span
                      className={cn(
                        "text-lg font-mono font-bold",
                        position.pnl >= 0
                          ? "text-hud-green"
                          : "text-hud-red"
                      )}
                    >
                      {position.pnl >= 0 ? "+" : ""}$
                      {formatCurrency(position.pnl)}
                    </span>
                    <span
                      className={cn(
                        "text-sm font-mono",
                        position.pnlPercent >= 0
                          ? "text-hud-green"
                          : "text-hud-red"
                      )}
                    >
                      ({position.pnlPercent >= 0 ? "+" : ""}
                      {position.pnlPercent.toFixed(2)}%)
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center py-6 text-muted-foreground">
                <Activity className="h-8 w-8 mb-2 opacity-40" />
                <p className="text-sm">No open position</p>
              </div>
            )}
          </div>
        </HudPanel>
      </div>

      {/* ---------------------------------------------------------------- */}
      {/* 5. Quick Stats Row */}
      {/* ---------------------------------------------------------------- */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-4">
          <p className="text-xs text-muted-foreground mb-1">Market Cap</p>
          <p className="text-lg font-mono font-bold text-white">&mdash;</p>
        </div>

        <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-4">
          <p className="text-xs text-muted-foreground mb-1">Volume 24h</p>
          <p className="text-lg font-mono font-bold text-white">&mdash;</p>
        </div>

        <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-4">
          <p className="text-xs text-muted-foreground mb-1">
            Signal Confidence
          </p>
          <p className="text-lg font-mono font-bold text-white">
            {signal
              ? `${(signal.confidence * 100).toFixed(1)}%`
              : "\u2014"}
          </p>
        </div>

        <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-4">
          <p className="text-xs text-muted-foreground mb-1">Feed Status</p>
          <Badge
            className={cn(
              "text-[10px] mt-1",
              feedStatus === "WS Live"
                ? "bg-hud-green/15 text-hud-green border-hud-green/30"
                : feedStatus === "REST"
                  ? "bg-hud-cyan/15 text-hud-cyan border-hud-cyan/30"
                  : "bg-yellow-500/15 text-yellow-400 border-yellow-500/30"
            )}
          >
            {feedStatus}
          </Badge>
        </div>
      </div>

      {/* ---------------------------------------------------------------- */}
      {/* 6. Related Assets */}
      {/* ---------------------------------------------------------------- */}
      <HudPanel title="RELATED ASSETS">
        <div className="p-4">
          <div className="flex flex-wrap gap-2">
            {relatedAssets.map((a) => (
              <Link key={a.symbol} href={`/asset/${a.symbol}`}>
                <Badge
                  variant="outline"
                  className="cursor-pointer hover:bg-muted/50 hover:text-white transition-colors text-sm px-3 py-1"
                >
                  {a.symbol}
                  <span className="ml-1.5 text-muted-foreground text-xs">
                    {a.name}
                  </span>
                </Badge>
              </Link>
            ))}
          </div>
        </div>
      </HudPanel>
    </div>
  );
}
