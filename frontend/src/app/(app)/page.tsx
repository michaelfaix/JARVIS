// =============================================================================
// src/app/(app)/page.tsx — Dashboard Page
// =============================================================================

"use client";

import { useCallback, useState } from "react";
import { AssetChart } from "@/components/chart/asset-chart";
import { TimeframeSlider, TIMEFRAMES } from "@/components/dashboard/timeframe-slider";
import { RegimeDisplay } from "@/components/dashboard/regime-display";
import {
  QualityScoreCard,
  SystemModeCard,
} from "@/components/dashboard/system-status";
import { StatCard } from "@/components/dashboard/stat-card";
import { AppHeader } from "@/components/layout/app-header";
import { useMetrics, useSystemStatus } from "@/hooks/use-jarvis";
import { useSignals } from "@/hooks/use-signals";
import { usePortfolio } from "@/hooks/use-portfolio";
import { usePrices } from "@/hooks/use-prices";
// useWebSocket for backend stream (optional)
import { inferRegime, type RegimeState } from "@/lib/types";
import { Watchlist } from "@/components/dashboard/watchlist";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  TrendingUp,
  TrendingDown,
  Wallet,
  ShieldAlert,
  Radio,
  Zap,
} from "lucide-react";

const CHART_ASSETS = [
  { symbol: "BTC", name: "Bitcoin", basePrice: 65000 },
  { symbol: "ETH", name: "Ethereum", basePrice: 3200 },
  { symbol: "SOL", name: "Solana", basePrice: 145 },
  { symbol: "SPY", name: "S&P 500 ETF", basePrice: 520 },
  { symbol: "GLD", name: "Gold ETF", basePrice: 215 },
] as const;

export default function DashboardPage() {
  const { status } = useSystemStatus(5000);
  const { metrics } = useMetrics(5000);
  const regime: RegimeState = status ? inferRegime(status.modus) : "RISK_ON";
  const { signals } = useSignals(regime, 10000);
  const { state: portfolio, unrealizedPnl, totalValue, winRate, drawdown } =
    usePortfolio();
  const { prices, wsConnected, binanceConnected } = usePrices(5000);
  const [selectedAsset, setSelectedAsset] = useState(0);
  const [timeframeIdx, setTimeframeIdx] = useState(4); // default: 4H Combined

  // Live price from chart (WS for crypto, sim for stocks)
  const [wsPrice, setWsPrice] = useState<number | null>(null);
  const handlePriceChange = useCallback(
    (price: number) => {
      setWsPrice(price);
    },
    []
  );

  const asset = CHART_ASSETS[selectedAsset];
  const chartInterval = TIMEFRAMES[timeframeIdx].value;

  const totalPnl = portfolio.realizedPnl + unrealizedPnl;
  const topSignals = [...signals]
    .sort((a, b) => b.confidence - a.confidence)
    .slice(0, 3);

  return (
    <>
      <AppHeader title="Dashboard" subtitle="Market Overview" />
      <div className="p-3 sm:p-4 md:p-6 space-y-4 md:space-y-6">
        {/* Top Row: Regime + System Mode + Quality */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <RegimeDisplay
            regime={regime}
            metaUncertainty={status?.meta_unsicherheit ?? 0}
            ece={status?.ece ?? 0}
            oodScore={status?.ood_score ?? 0}
          />
          <SystemModeCard
            modus={status?.modus ?? "NORMAL"}
            vorhersagenAktiv={status?.vorhersagen_aktiv ?? true}
            konfidenzMultiplikator={status?.konfidenz_multiplikator ?? 1.0}
            entscheidungsCount={status?.entscheidungs_count ?? 0}
          />
          <QualityScoreCard metrics={metrics} />
        </div>

        {/* USP: Timeframe Slider */}
        <Card className="bg-card/50 border-border/50">
          <CardContent className="pt-5 pb-4">
            <TimeframeSlider value={timeframeIdx} onChange={setTimeframeIdx} />
          </CardContent>
        </Card>

        {/* Multi-Asset Chart */}
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
              {/* Asset Selector Tabs */}
              <div className="flex flex-wrap gap-1">
                {CHART_ASSETS.map((a, i) => (
                  <button
                    key={a.symbol}
                    onClick={() => {
                      setSelectedAsset(i);
                      setWsPrice(null);
                    }}
                    className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                      selectedAsset === i
                        ? "bg-blue-600/20 text-blue-400"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground"
                    }`}
                  >
                    {a.symbol}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-[10px]">
                  {TIMEFRAMES[timeframeIdx].label} / {TIMEFRAMES[timeframeIdx].strategyLabel}
                </Badge>
                <div className="flex items-center gap-1.5">
                  <Zap
                    className={`h-3 w-3 ${
                      wsConnected
                        ? "text-green-400"
                        : binanceConnected
                          ? "text-blue-400"
                          : "text-yellow-400"
                    }`}
                  />
                  <span className="text-[10px]">
                    {wsConnected ? "WS Live" : binanceConnected ? "REST" : "Live Sim"}
                  </span>
                </div>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <AssetChart
              key={`${asset.symbol}-${chartInterval}`}
              symbol={asset.symbol}
              name={asset.name}
              basePrice={asset.basePrice}
              livePrice={wsPrice ?? prices[asset.symbol]}
              regime={regime}
              height={400}
              interval={chartInterval}
              onPriceChange={handlePriceChange}
            />
          </CardContent>
        </Card>

        {/* Portfolio Summary + Top Signals */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Portfolio Summary */}
          <Card className="bg-card/50 border-border/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <Wallet className="h-4 w-4" />
                Portfolio Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-lg bg-background/50 p-3">
                  <div className="text-xs text-muted-foreground mb-1">
                    Total Value
                  </div>
                  <div className="text-lg font-bold font-mono text-white">
                    $
                    {totalValue.toLocaleString("en-US", {
                      maximumFractionDigits: 0,
                    })}
                  </div>
                </div>
                <div className="rounded-lg bg-background/50 p-3">
                  <div className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                    {totalPnl >= 0 ? (
                      <TrendingUp className="h-3 w-3 text-green-400" />
                    ) : (
                      <TrendingDown className="h-3 w-3 text-red-400" />
                    )}
                    Total P&L
                  </div>
                  <div
                    className={`text-lg font-bold font-mono ${
                      totalPnl >= 0 ? "text-green-400" : "text-red-400"
                    }`}
                  >
                    {totalPnl >= 0 ? "+" : ""}$
                    {Math.abs(totalPnl).toFixed(0)}
                  </div>
                </div>
                <div className="rounded-lg bg-background/50 p-3">
                  <div className="text-xs text-muted-foreground mb-1">
                    Open Positions
                  </div>
                  <div className="text-lg font-bold font-mono text-blue-400">
                    {portfolio.positions.length}
                  </div>
                </div>
                <div className="rounded-lg bg-background/50 p-3">
                  <div className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                    <ShieldAlert className="h-3 w-3" />
                    Drawdown
                  </div>
                  <div
                    className={`text-lg font-bold font-mono ${
                      drawdown > 5
                        ? "text-red-400"
                        : drawdown > 0
                        ? "text-yellow-400"
                        : "text-green-400"
                    }`}
                  >
                    {drawdown.toFixed(2)}%
                  </div>
                </div>
              </div>
              {portfolio.closedTrades.length > 0 && (
                <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
                  <span>
                    Win Rate:{" "}
                    <span
                      className={`font-mono ${
                        winRate >= 50 ? "text-green-400" : "text-red-400"
                      }`}
                    >
                      {winRate.toFixed(0)}%
                    </span>
                  </span>
                  <span>
                    Trades:{" "}
                    <span className="font-mono text-white">
                      {portfolio.closedTrades.length}
                    </span>
                  </span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Top Signals */}
          <Card className="bg-card/50 border-border/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <Radio className="h-4 w-4" />
                Top Signals
                <Badge variant="outline" className="ml-auto text-[10px]">
                  {signals.length} active
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {topSignals.length === 0 ? (
                <div className="text-sm text-muted-foreground py-4 text-center">
                  No signals available. Start backend to generate signals.
                </div>
              ) : (
                topSignals.map((signal) => (
                  <div
                    key={signal.id}
                    className="flex items-center gap-3 rounded-lg bg-background/50 p-3"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-white text-sm">
                          {signal.asset}
                        </span>
                        <Badge
                          className={`text-[10px] ${
                            signal.direction === "LONG"
                              ? "bg-green-500/20 text-green-400 border-green-500/30"
                              : "bg-red-500/20 text-red-400 border-red-500/30"
                          }`}
                        >
                          {signal.direction}
                        </Badge>
                        {signal.isOod && (
                          <Badge className="text-[10px] bg-yellow-500/20 text-yellow-400 border-yellow-500/30">
                            OOD
                          </Badge>
                        )}
                      </div>
                      <div className="text-[10px] text-muted-foreground mt-1">
                        Entry: $
                        {signal.entry.toLocaleString("en-US", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                        {" | "}Quality: {(signal.qualityScore * 100).toFixed(0)}
                      </div>
                    </div>
                    <div className="w-24">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-muted-foreground">Conf</span>
                        <span className="font-mono text-white">
                          {(signal.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
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
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        {/* Watchlist */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <Watchlist
              prices={prices}
              signals={signals.map((s) => ({
                asset: s.asset,
                direction: s.direction,
                confidence: s.confidence,
              }))}
            />
          </div>
          <div className="lg:col-span-2">
            {/* Stats Row */}
            <div className="grid grid-cols-2 gap-4">
          <StatCard
            label="Predictions Today"
            value={status?.entscheidungs_count?.toString() ?? "0"}
          />
          <StatCard
            label="Model Calibration"
            value={
              metrics
                ? `${(metrics.calibration_component * 100).toFixed(1)}%`
                : "—"
            }
          />
          <StatCard
            label="Data Quality"
            value={
              metrics
                ? `${(metrics.data_quality_component * 100).toFixed(1)}%`
                : "—"
            }
          />
          <StatCard label="System Uptime" value="100%" />
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
