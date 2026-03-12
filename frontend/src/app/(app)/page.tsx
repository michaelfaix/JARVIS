// =============================================================================
// src/app/(app)/page.tsx — Dashboard Page
// =============================================================================

"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
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
import { useSentiment } from "@/hooks/use-sentiment";
import { useAlerts } from "@/hooks/use-alerts";
import { MarketPulse } from "@/components/dashboard/market-pulse";
// useWebSocket for backend stream (optional)
import { Watchlist } from "@/components/dashboard/watchlist";
import { PnlTicker } from "@/components/dashboard/pnl-ticker";
import { ActivityFeed } from "@/components/dashboard/activity-feed";
import { MetricTooltip } from "@/components/ui/metric-tooltip";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ApiOfflineBanner } from "@/components/ui/api-offline-banner";
import {
  TrendingUp,
  TrendingDown,
  Wallet,
  ShieldAlert,
  Radio,
  Zap,
  RefreshCw,
  Bell,
  ArrowRight,
} from "lucide-react";

const CHART_ASSETS = [
  { symbol: "BTC", name: "Bitcoin", basePrice: 65000 },
  { symbol: "ETH", name: "Ethereum", basePrice: 3200 },
  { symbol: "SOL", name: "Solana", basePrice: 145 },
  { symbol: "SPY", name: "S&P 500 ETF", basePrice: 520 },
  { symbol: "GLD", name: "Gold ETF", basePrice: 215 },
] as const;

// ---------------------------------------------------------------------------
// Relative time helper
// ---------------------------------------------------------------------------
function relativeTime(ts: number | null): string {
  if (!ts) return "";
  const diff = Math.floor((Date.now() - ts) / 1000);
  if (diff < 5) return "just now";
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

export default function DashboardPage() {
  const router = useRouter();
  const {
    status,
    regime,
    loading: statusLoading,
    error: statusError,
    lastUpdated: statusUpdated,
    refresh: refreshStatus,
  } = useSystemStatus(5000);
  const {
    metrics,
    loading: metricsLoading,
    error: metricsError,
    lastUpdated: metricsUpdated,
    refresh: refreshMetrics,
  } = useMetrics(5000);
  const {
    signals,
    loading: signalsLoading,
    error: signalsError,
    refresh: refreshSignals,
  } = useSignals(regime, 10000);

  const backendOffline = !!(statusError || metricsError || signalsError);
  const { state: portfolio, unrealizedPnl, totalValue, winRate, drawdown } =
    usePortfolio();
  const { prices, wsConnected, binanceConnected } = usePrices(5000);
  const sentimentData = useSentiment(prices);
  const { activeAlerts } = useAlerts();
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
  const topSignals = useMemo(
    () =>
      [...signals].sort((a, b) => b.confidence - a.confidence).slice(0, 3),
    [signals]
  );

  // Approaching alerts (within 5% of target)
  const approachingAlerts = useMemo(() => {
    return activeAlerts
      .filter((a) => {
        const price = prices[a.asset];
        if (!price) return false;
        const dist = Math.abs(price - a.targetPrice) / a.targetPrice;
        return dist < 0.05;
      })
      .slice(0, 3);
  }, [activeAlerts, prices]);

  // Refresh all — keyboard shortcut "R"
  const refreshAll = useCallback(() => {
    refreshStatus();
    refreshMetrics();
    refreshSignals();
  }, [refreshStatus, refreshMetrics, refreshSignals]);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      // Only trigger on 'R' if not in an input/textarea
      if (
        e.key === "r" &&
        !e.ctrlKey &&
        !e.metaKey &&
        !e.altKey &&
        !(e.target instanceof HTMLInputElement) &&
        !(e.target instanceof HTMLTextAreaElement)
      ) {
        refreshAll();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [refreshAll]);

  // Relative time ticker — force re-render every 10s for "Xs ago" updates
  const [, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 10000);
    return () => clearInterval(id);
  }, []);

  return (
    <>
      <AppHeader title="Dashboard" subtitle="Market Overview" />
      <div className="p-3 sm:p-4 md:p-6 space-y-4 md:space-y-6">
        {/* Open P&L Ticker */}
        <PnlTicker positions={portfolio.positions} prices={prices} />

        {backendOffline && <ApiOfflineBanner />}

        {/* Approaching Alerts */}
        {approachingAlerts.length > 0 && (
          <div className="flex items-center gap-2 rounded-lg bg-blue-500/10 border border-blue-500/20 px-4 py-2 text-sm text-blue-400">
            <Bell className="h-4 w-4 shrink-0" />
            <div className="flex-1 flex flex-wrap gap-x-4 gap-y-1">
              {approachingAlerts.map((a) => (
                <span key={a.id} className="whitespace-nowrap">
                  {a.asset} approaching ${a.targetPrice.toLocaleString()}
                  {a.condition === "above" ? " ↑" : " ↓"}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Top Row: Regime + System Mode + Quality + Sentiment */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          <RegimeDisplay
            regime={regime}
            metaUncertainty={status?.meta_unsicherheit ?? 0}
            ece={status?.ece ?? 0}
            oodScore={status?.ood_score ?? 0}
            loading={statusLoading}
          />
          <SystemModeCard
            modus={status?.modus ?? "NORMAL"}
            vorhersagenAktiv={status?.vorhersagen_aktiv ?? true}
            konfidenzMultiplikator={status?.konfidenz_multiplikator ?? 1.0}
            entscheidungsCount={status?.entscheidungs_count ?? 0}
            loading={statusLoading}
          />
          <QualityScoreCard metrics={metrics} loading={metricsLoading} />
          <MarketPulse data={sentimentData} />
        </div>

        {/* Updated timestamp + Refresh */}
        <div className="flex items-center justify-end gap-3 text-[10px] text-muted-foreground">
          {statusUpdated && (
            <span>Status: {relativeTime(statusUpdated)}</span>
          )}
          {metricsUpdated && (
            <span>Metrics: {relativeTime(metricsUpdated)}</span>
          )}
          <button
            onClick={refreshAll}
            className="flex items-center gap-1 text-muted-foreground hover:text-white transition-colors"
            title="Refresh all (R)"
          >
            <RefreshCw className="h-3 w-3" />
            Refresh
          </button>
        </div>

        {/* USP: Timeframe Slider — click navigates to charts */}
        <Card className="bg-card/50 border-border/50">
          <CardContent className="pt-5 pb-4">
            <TimeframeSlider
              value={timeframeIdx}
              onChange={(idx) => {
                setTimeframeIdx(idx);
              }}
            />
            <button
              onClick={() => router.push(`/charts`)}
              className="mt-2 flex items-center gap-1 text-[10px] text-muted-foreground hover:text-blue-400 transition-colors"
            >
              Open in Charts
              <ArrowRight className="h-2.5 w-2.5" />
            </button>
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
                    <MetricTooltip term="Drawdown">
                      <ShieldAlert className="h-3 w-3" />
                      Drawdown
                    </MetricTooltip>
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
                  <MetricTooltip term="Win Rate">
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
                  </MetricTooltip>
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

          {/* Top Signals — click navigates to /signals */}
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
              {signalsLoading && topSignals.length === 0 ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="rounded-lg bg-background/50 p-3 animate-pulse h-16" />
                  ))}
                </div>
              ) : topSignals.length === 0 ? (
                <div className="text-sm text-muted-foreground py-4 text-center">
                  No signals available. Start backend to generate signals.
                </div>
              ) : (
                topSignals.map((signal) => (
                  <button
                    key={signal.id}
                    onClick={() => router.push("/signals")}
                    className="flex items-center gap-3 rounded-lg bg-background/50 p-3 w-full text-left hover:bg-background/70 transition-colors group"
                  >
                    <div className="flex-1 min-w-0">
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
                      <div className="text-[10px] text-muted-foreground mt-1 flex flex-wrap gap-x-2">
                        <span>
                          Entry: $
                          {signal.entry.toLocaleString("en-US", {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </span>
                        <span className="text-red-400/70">
                          SL: $
                          {signal.stopLoss.toLocaleString("en-US", {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </span>
                        <span className="text-green-400/70">
                          TP: $
                          {signal.takeProfit.toLocaleString("en-US", {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </span>
                      </div>
                    </div>
                    <div className="w-24 shrink-0">
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
                    <ArrowRight className="h-3.5 w-3.5 text-muted-foreground/30 group-hover:text-blue-400 transition-colors shrink-0" />
                  </button>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        {/* Watchlist + Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 space-y-6">
            <Watchlist
              prices={prices}
              signals={signals.map((s) => ({
                asset: s.asset,
                direction: s.direction,
                confidence: s.confidence,
              }))}
            />
            <ActivityFeed
              closedTrades={portfolio.closedTrades.map((t) => ({
                id: t.id,
                asset: t.asset,
                direction: t.direction,
                pnl: t.pnl,
                closedAt: t.closedAt,
              }))}
              openPositions={portfolio.positions.map((p) => ({
                asset: p.asset,
                direction: p.direction,
                openedAt: p.openedAt,
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
