// =============================================================================
// src/app/(app)/page.tsx — Dashboard Page
// =============================================================================

"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
import { useOrders } from "@/hooks/use-orders";
import { useAutoSLTP } from "@/hooks/use-auto-sl-tp";
import { useNotifications } from "@/hooks/use-notifications";
import { useFeedback } from "@/hooks/use-feedback";
import { MarketPulse } from "@/components/dashboard/market-pulse";
import { SignalQuality } from "@/components/dashboard/signal-quality";
import { Watchlist } from "@/components/dashboard/watchlist";
import { PnlTicker } from "@/components/dashboard/pnl-ticker";
import { ActivityFeed } from "@/components/dashboard/activity-feed";
import { StrategyControl } from "@/components/dashboard/strategy-control";
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
  Activity,
  Check,
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
    apiLatencyMs,
    refresh: refreshStatus,
  } = useSystemStatus(5000);
  const {
    metrics,
    loading: metricsLoading,
    error: metricsError,
    lastUpdated: metricsUpdated,
    refresh: refreshMetrics,
  } = useMetrics(5000);
  const { prices, priceHistory, wsConnected, binanceConnected } = usePrices(5000);

  const {
    signals,
    loading: signalsLoading,
    backendOnline,
    refresh: refreshSignals,
  } = useSignals(regime, 10000, prices, priceHistory);

  const backendOffline = !!(statusError || metricsError) && !backendOnline;
  const { state: portfolio, unrealizedPnl, totalValue, winRate, drawdown, openPosition, closePosition, updatePrices } =
    usePortfolio();
  const { checkOrders, cleanupOrders } = useOrders(openPosition);
  const { push: pushNotification } = useNotifications();
  const { checkSLTP } = useAutoSLTP(portfolio.positions, closePosition, pushNotification);
  // Feedback loop: auto-send trade outcomes to backend ML
  const { accuracyByAsset } = useFeedback(portfolio.closedTrades);
  const sentimentData = useSentiment(prices, priceHistory);
  const { activeAlerts } = useAlerts();

  // --- Trading Engine: 1s tick for P&L updates, order fills, SL/TP checks ---
  const pricesTickRef = useRef(prices);
  pricesTickRef.current = prices;
  useEffect(() => {
    const tick = () => {
      const p = pricesTickRef.current;
      if (Object.keys(p).length === 0) return;
      updatePrices(p);
      checkOrders(p);
      checkSLTP(p);
    };
    tick();
    const id = setInterval(tick, 1000);
    const cleanupId = setInterval(cleanupOrders, 5 * 60 * 1000);
    return () => { clearInterval(id); clearInterval(cleanupId); };
  }, [updatePrices, checkOrders, checkSLTP, cleanupOrders]);

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

  // Quick-Trade: accept a signal and open a position
  const acceptSignal = useCallback(
    (signal: (typeof signals)[0]) => {
      const capitalPerTrade = portfolio.availableCapital * 0.05; // 5% per trade
      if (capitalPerTrade < 10) return; // minimum $10
      const size = capitalPerTrade / signal.entry;
      openPosition({
        asset: signal.asset,
        direction: signal.direction,
        entryPrice: signal.entry,
        size,
        capitalAllocated: capitalPerTrade,
        openedAt: new Date().toISOString(),
      });
    },
    [portfolio.availableCapital, openPosition]
  );

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

        {backendOffline && (
          <ApiOfflineBanner
            message={
              !backendOnline
                ? "JARVIS Backend offline — signals are locally derived from market data"
                : "JARVIS Backend partially unavailable — some metrics may be stale"
            }
          />
        )}

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
            ece={status?.ece ?? 0}
            oodScore={status?.ood_score ?? 0}
            metaUncertainty={status?.meta_unsicherheit ?? 0}
            loading={statusLoading}
            backendOnline={backendOnline}
          />
          <QualityScoreCard metrics={metrics} loading={metricsLoading} />
          <MarketPulse data={sentimentData} />
        </div>

        {/* Updated timestamp + API latency + Refresh */}
        <div className="flex items-center justify-end gap-3 text-[10px] text-muted-foreground">
          {statusUpdated && (
            <span>Status: {relativeTime(statusUpdated)}</span>
          )}
          {metricsUpdated && (
            <span>Metrics: {relativeTime(metricsUpdated)}</span>
          )}
          {apiLatencyMs !== null && (
            <span className="flex items-center gap-1">
              <Activity className="h-2.5 w-2.5" />
              API: {apiLatencyMs}ms
            </span>
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

        {/* Strategy Control Panel */}
        <StrategyControl />

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
                topSignals.map((signal) => {
                  const alreadyOpen = portfolio.positions.some(
                    (p) => p.asset === signal.asset && p.direction === signal.direction
                  );
                  return (
                    <div
                      key={signal.id}
                      className="flex items-center gap-3 rounded-lg bg-background/50 p-3 group"
                    >
                      <button
                        onClick={() => router.push("/signals")}
                        className="flex items-center gap-3 flex-1 min-w-0 text-left hover:opacity-80 transition-opacity"
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
                      </button>
                      {alreadyOpen ? (
                        <span className="flex items-center gap-1 text-[10px] text-green-400/60 shrink-0" title="Position already open">
                          <Check className="h-3 w-3" />
                          Open
                        </span>
                      ) : (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            acceptSignal(signal);
                          }}
                          className="shrink-0 px-2 py-1 rounded text-[10px] font-medium bg-blue-600/20 text-blue-400 border border-blue-500/30 hover:bg-blue-600/40 transition-colors"
                          title="Quick-Trade: Open position with 5% capital"
                        >
                          Trade
                        </button>
                      )}
                      <ArrowRight className="h-3.5 w-3.5 text-muted-foreground/30 group-hover:text-blue-400 transition-colors shrink-0" />
                    </div>
                  );
                })
              )}
            </CardContent>
          </Card>
        </div>

        {/* Watchlist + Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 space-y-6">
            <Watchlist
              prices={prices}
              priceHistory={priceHistory}
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
          <div className="lg:col-span-2 space-y-6">
            {/* Signal Quality Panel */}
            <SignalQuality
              signals={signals}
              metrics={metrics}
              accuracyByAsset={accuracyByAsset}
              backendOnline={backendOnline}
            />
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
