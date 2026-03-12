// =============================================================================
// src/app/(app)/charts/page.tsx — Dedicated Charts Page with Multi-Timeframe
//
// Live WebSocket prices flow into the chart (live candle) AND trigger
// JARVIS /predict signal refresh so signals stay in sync with price.
// =============================================================================

"use client";

import { useCallback, useRef, useState } from "react";
import { AppHeader } from "@/components/layout/app-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AssetChart } from "@/components/chart/asset-chart";
import {
  IndicatorPanel,
  DEFAULT_INDICATORS,
  type IndicatorConfig,
} from "@/components/chart/indicator-panel";
import { usePrices } from "@/hooks/use-prices";
import { useSystemStatus } from "@/hooks/use-jarvis";
import { useSignals } from "@/hooks/use-signals";
import { inferRegime, type RegimeState } from "@/lib/types";
import { DEFAULT_ASSETS } from "@/lib/constants";
import {
  CandlestickChart,
  Zap,
  TrendingUp,
  TrendingDown,
} from "lucide-react";

const INTERVALS = [
  { value: "1m", label: "1m" },
  { value: "5m", label: "5m" },
  { value: "15m", label: "15m" },
  { value: "1h", label: "1H" },
  { value: "4h", label: "4H" },
  { value: "1d", label: "1D" },
  { value: "1w", label: "1W" },
] as const;

export default function ChartsPage() {
  const { prices, wsConnected, binanceConnected } = usePrices(5000);
  const { status } = useSystemStatus(5000);
  const regime: RegimeState = status ? inferRegime(status.modus) : "RISK_ON";
  const { signals, refresh: refreshSignals } = useSignals(regime, 10000);

  const [selectedAsset, setSelectedAsset] = useState(0);
  const [chartInterval, setChartInterval] = useState("1d");
  const [indicators, setIndicators] = useState<IndicatorConfig>({
    ...DEFAULT_INDICATORS,
  });

  // Live price from chart WebSocket (updates ~1/s)
  const [wsPrice, setWsPrice] = useState<number | null>(null);

  // Debounce signal refresh: at most once per 5 seconds when price changes
  const lastRefreshRef = useRef(0);
  const handlePriceChange = useCallback(
    (price: number) => {
      setWsPrice(price);
      const now = Date.now();
      if (now - lastRefreshRef.current > 5000) {
        lastRefreshRef.current = now;
        refreshSignals();
      }
    },
    [refreshSignals]
  );

  const asset = DEFAULT_ASSETS[selectedAsset];
  const signal = signals.find((s) => s.asset === asset.symbol);
  const currentPrice = wsPrice ?? prices[asset.symbol] ?? asset.price;

  return (
    <>
      <AppHeader title="Charts" subtitle="Technical Analysis" />
      <div className="p-3 sm:p-4 md:p-6 space-y-3 md:space-y-4">
        {/* Controls Bar */}
        <Card className="bg-card/50 border-border/50">
          <CardContent className="py-3 px-4">
            <div className="flex items-center justify-between flex-wrap gap-3">
              {/* Asset selector */}
              <div className="flex items-center gap-1 flex-wrap">
                {DEFAULT_ASSETS.map((a, i) => (
                  <button
                    key={a.symbol}
                    onClick={() => {
                      setSelectedAsset(i);
                      setWsPrice(null); // reset WS price on asset change
                    }}
                    className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                      selectedAsset === i
                        ? "bg-blue-600/20 text-blue-400"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground"
                    }`}
                  >
                    {a.symbol}
                  </button>
                ))}
              </div>

              {/* Timeframe + Status */}
              <div className="flex items-center gap-3">
                {/* Interval selector */}
                <div className="flex items-center gap-0.5 rounded-lg border border-border/50 p-0.5">
                  {INTERVALS.map((tf) => (
                    <button
                      key={tf.value}
                      onClick={() => {
                        setChartInterval(tf.value);
                        setWsPrice(null); // reset WS price on interval change
                      }}
                      className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${
                        chartInterval === tf.value
                          ? "bg-blue-600/20 text-blue-400"
                          : "text-muted-foreground hover:text-white"
                      }`}
                    >
                      {tf.label}
                    </button>
                  ))}
                </div>

                {/* Indicator selector */}
                <IndicatorPanel
                  value={indicators}
                  onChange={setIndicators}
                />

                {/* Feed status */}
                <div className="flex items-center gap-1.5">
                  <Zap
                    className={`h-3 w-3 ${
                      wsConnected
                        ? "text-green-400"
                        : binanceConnected
                          ? "text-green-400"
                          : "text-yellow-400"
                    }`}
                  />
                  <span className="text-[10px] text-muted-foreground">
                    {wsConnected
                      ? "WS Live"
                      : binanceConnected
                        ? "REST"
                        : "Synthetic"}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Asset Info Bar */}
        <div className="flex items-center gap-2 sm:gap-4 px-1 flex-wrap">
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold text-white">
              {asset.symbol}
            </span>
            <span className="text-xs text-muted-foreground">{asset.name}</span>
          </div>
          <span className="text-xl font-mono font-bold text-white">
            $
            {currentPrice.toLocaleString("en-US", {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </span>
          {signal && (
            <Badge
              className={`text-[10px] ${
                signal.direction === "LONG"
                  ? "bg-green-500/20 text-green-400 border-green-500/30"
                  : "bg-red-500/20 text-red-400 border-red-500/30"
              }`}
            >
              {signal.direction === "LONG" ? (
                <TrendingUp className="h-3 w-3 mr-1" />
              ) : (
                <TrendingDown className="h-3 w-3 mr-1" />
              )}
              {signal.direction} {(signal.confidence * 100).toFixed(0)}%
            </Badge>
          )}
          <Badge variant="outline" className="text-[10px]">
            {INTERVALS.find((i) => i.value === chartInterval)?.label}
          </Badge>
        </div>

        {/* Main Chart — key forces full remount on asset/interval change */}
        <Card className="bg-card/50 border-border/50">
          <CardContent className="pt-4">
            <AssetChart
              key={`${asset.symbol}-${chartInterval}`}
              symbol={asset.symbol}
              name={asset.name}
              basePrice={asset.price}
              livePrice={currentPrice}
              regime={regime}
              height={500}
              interval={chartInterval}
              onPriceChange={handlePriceChange}
              indicators={indicators}
            />
          </CardContent>
        </Card>

        {/* Signal Details */}
        {signal && (
          <Card className="bg-card/50 border-border/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <CandlestickChart className="h-4 w-4" />
                Signal Details — {asset.symbol}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="rounded-lg bg-background/50 p-3 text-center">
                  <div className="text-[10px] text-muted-foreground mb-1">
                    Direction
                  </div>
                  <Badge
                    className={
                      signal.direction === "LONG"
                        ? "bg-green-500/20 text-green-400 border-green-500/30"
                        : "bg-red-500/20 text-red-400 border-red-500/30"
                    }
                  >
                    {signal.direction}
                  </Badge>
                </div>
                <div className="rounded-lg bg-background/50 p-3 text-center">
                  <div className="text-[10px] text-muted-foreground mb-1">
                    Entry
                  </div>
                  <div className="text-sm font-mono text-white">
                    $
                    {signal.entry.toLocaleString("en-US", {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </div>
                </div>
                <div className="rounded-lg bg-background/50 p-3 text-center">
                  <div className="text-[10px] text-muted-foreground mb-1">
                    Stop Loss
                  </div>
                  <div className="text-sm font-mono text-red-400">
                    $
                    {signal.stopLoss.toLocaleString("en-US", {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </div>
                </div>
                <div className="rounded-lg bg-background/50 p-3 text-center">
                  <div className="text-[10px] text-muted-foreground mb-1">
                    Take Profit
                  </div>
                  <div className="text-sm font-mono text-green-400">
                    $
                    {signal.takeProfit.toLocaleString("en-US", {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </div>
                </div>
                <div className="rounded-lg bg-background/50 p-3 text-center">
                  <div className="text-[10px] text-muted-foreground mb-1">
                    Confidence
                  </div>
                  <div
                    className={`text-sm font-mono ${
                      signal.confidence > 0.7
                        ? "text-green-400"
                        : signal.confidence > 0.4
                          ? "text-yellow-400"
                          : "text-red-400"
                    }`}
                  >
                    {(signal.confidence * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </>
  );
}
