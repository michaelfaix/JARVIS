// =============================================================================
// src/app/(app)/page.tsx — Dashboard Page (HUD Redesign)
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
import { HudTopbar } from "@/components/layout/hud-topbar";
import { HudPanel } from "@/components/ui/hud-panel";
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
import { TopSignalsHud } from "@/components/dashboard/top-signals-hud";
import { Watchlist } from "@/components/dashboard/watchlist";
import { PnlTicker } from "@/components/dashboard/pnl-ticker";
import { ActivityFeed } from "@/components/dashboard/activity-feed";
import { StrategyControl } from "@/components/dashboard/strategy-control";
import type { JarvisTipsContext } from "@/components/chart/asset-chart";
import dynamic from "next/dynamic";
const CoPilotPanel = dynamic(() => import("@/components/copilot/copilot-panel").then((m) => m.CoPilotPanel), { ssr: false });
const CoPilotTrigger = dynamic(() => import("@/components/copilot/copilot-trigger").then((m) => m.CoPilotTrigger), { ssr: false });
import { CoPilotEmbed } from "@/components/copilot/copilot-embed";
import { useCoPilot } from "@/hooks/use-copilot";
import { useProactiveWarnings } from "@/hooks/use-proactive-warnings";
import { useStrategy } from "@/hooks/use-strategy";
import { MetricTooltip } from "@/components/ui/metric-tooltip";
import { Badge } from "@/components/ui/badge";
import { ApiOfflineBanner } from "@/components/ui/api-offline-banner";
import { loadJSON, saveJSON } from "@/lib/storage";
import {
  TrendingUp,
  TrendingDown,
  ShieldAlert,
  Zap,
  RefreshCw,
  Bell,
  ArrowRight,
  Activity,
  Star,
} from "lucide-react";

const CHART_ASSETS = [
  { symbol: "BTC", name: "Bitcoin", basePrice: 65000 },
  { symbol: "ETH", name: "Ethereum", basePrice: 3200 },
  { symbol: "SOL", name: "Solana", basePrice: 145 },
  { symbol: "SPY", name: "S&P 500 ETF", basePrice: 520 },
  { symbol: "GLD", name: "Gold ETF", basePrice: 215 },
  { symbol: "OIL", name: "Crude Oil", basePrice: 78 },
] as const;

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
  const { accuracyByAsset } = useFeedback(portfolio.closedTrades);
  const sentimentData = useSentiment(prices, priceHistory);
  const { activeAlerts, addAlert } = useAlerts();
  const strategy = useStrategy();
  const [copilotOpen, setCopilotOpen] = useState(false);

  // --- Trading Engine: 1s tick ---
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

  // --- Favorite Chart ---
  interface FavoriteChart { assetIdx: number; timeframeIdx: number; }
  const FAV_DEFAULT: FavoriteChart = useMemo(() => ({ assetIdx: 0, timeframeIdx: 4 }), []);
  const [selectedAsset, setSelectedAsset] = useState(0);
  const [timeframeIdx, setTimeframeIdx] = useState(4);
  const [favLoaded, setFavLoaded] = useState(false);

  useEffect(() => {
    const fav = loadJSON<FavoriteChart>("jarvis:favorite-chart", FAV_DEFAULT);
    setSelectedAsset(fav.assetIdx);
    setTimeframeIdx(fav.timeframeIdx);
    setFavLoaded(true);
  }, [FAV_DEFAULT]);

  const saveFavorite = useCallback(() => {
    saveJSON("jarvis:favorite-chart", { assetIdx: selectedAsset, timeframeIdx });
  }, [selectedAsset, timeframeIdx]);

  const isCurrentFavorite = useMemo(() => {
    if (!favLoaded) return false;
    const fav = loadJSON<FavoriteChart>("jarvis:favorite-chart", FAV_DEFAULT);
    return fav.assetIdx === selectedAsset && fav.timeframeIdx === timeframeIdx;
  }, [selectedAsset, timeframeIdx, FAV_DEFAULT, favLoaded]);

  const [wsPrice, setWsPrice] = useState<number | null>(null);
  const handlePriceChange = useCallback((price: number) => setWsPrice(price), []);

  const asset = CHART_ASSETS[selectedAsset];
  const chartInterval = TIMEFRAMES[timeframeIdx].value;

  const strategyOverlay = useMemo(
    () => ({
      strategy: strategy.state.selectedStrategy,
      slPercent: strategy.state.params.slPercent,
      tpPercent: strategy.state.params.tpPercent,
      rsiLength: strategy.state.params.rsiLength,
      emaFast: strategy.state.params.emaFast,
      emaSlow: strategy.state.params.emaSlow,
    }),
    [strategy.state.selectedStrategy, strategy.state.params.slPercent, strategy.state.params.tpPercent, strategy.state.params.rsiLength, strategy.state.params.emaFast, strategy.state.params.emaSlow]
  );

  const jarvisTipsCtx: JarvisTipsContext = useMemo(
    () => ({
      regime,
      ece: status?.ece ?? 0,
      oodScore: status?.ood_score ?? 0,
      metaUncertainty: status?.meta_unsicherheit ?? 0,
      sentiment: sentimentData ? sentimentData.crypto.momentum.score / 100 : null,
      strategy: strategy.state.selectedStrategy,
    }),
    [regime, status?.ece, status?.ood_score, status?.meta_unsicherheit, sentimentData, strategy.state.selectedStrategy]
  );

  // --- Co-Pilot ---
  const topSig = useMemo(() => {
    const sorted = [...signals].sort((a, b) => b.confidence - a.confidence);
    return sorted[0] ?? null;
  }, [signals]);

  const copilot = useCoPilot({
    regime,
    ece: status?.ece ?? 0,
    oodScore: status?.ood_score ?? 0,
    metaUncertainty: status?.meta_unsicherheit ?? 0,
    strategy: strategy.state.selectedStrategy,
    selectedAsset: asset.symbol,
    interval: chartInterval,
    slPercent: strategy.state.params.slPercent,
    tpPercent: strategy.state.params.tpPercent,
    currentPrice: wsPrice ?? prices[asset.symbol] ?? asset.basePrice,
    totalValue,
    drawdown,
    positionCount: portfolio.positions.length,
    closedTradeCount: portfolio.closedTrades.length,
    realizedPnl: portfolio.realizedPnl,
    winRate: portfolio.closedTrades.length > 0 ? (portfolio.closedTrades.filter((t) => t.pnl > 0).length / portfolio.closedTrades.length) * 100 : 0,
    signalCount: signals.length,
    topSignalAsset: topSig?.asset ?? null,
    topSignalDirection: topSig?.direction ?? null,
    topSignalConfidence: topSig?.confidence ?? 0,
    candles: [],
    addAlert,
  });

  useProactiveWarnings({
    regime,
    oodScore: status?.ood_score ?? 0,
    positions: portfolio.positions.map((p) => ({ asset: p.asset, direction: p.direction, entryPrice: p.entryPrice })),
    prices,
    slPercent: strategy.state.params.slPercent,
    tpPercent: strategy.state.params.tpPercent,
    topSignalConfidence: topSig?.confidence ?? 0,
    topSignalAsset: topSig?.asset ?? null,
    topSignalDirection: topSig?.direction ?? null,
    push: pushNotification,
  });

  const totalPnl = portfolio.realizedPnl + unrealizedPnl;

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

  const acceptSignal = useCallback(
    (signal: (typeof signals)[0]) => {
      const capitalPerTrade = portfolio.availableCapital * 0.05;
      if (capitalPerTrade < 10) return;
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

  const refreshAll = useCallback(() => {
    refreshStatus();
    refreshMetrics();
    refreshSignals();
  }, [refreshStatus, refreshMetrics, refreshSignals]);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "r" && !e.ctrlKey && !e.metaKey && !e.altKey && !(e.target instanceof HTMLInputElement) && !(e.target instanceof HTMLTextAreaElement)) {
        refreshAll();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [refreshAll]);

  const [, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 10000);
    return () => clearInterval(id);
  }, []);

  const sentimentValue = sentimentData ? sentimentData[sentimentData.activeTab].sentiment.value : 50;

  return (
    <>
      {/* HUD Topbar: desktop only */}
      <HudTopbar
        wsConnected={wsConnected}
        regime={regime}
        sentimentValue={sentimentValue}
        apiLatencyMs={apiLatencyMs}
      />

      {/* Mobile AppHeader */}
      <div className="md:hidden">
        <AppHeader title="Dashboard" subtitle="Market Overview" />
      </div>

      <div className="p-2 sm:p-3 md:p-4 space-y-3">
        {/* P&L Ticker */}
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
          <div className="flex items-center gap-2 rounded border border-hud-cyan/20 bg-hud-cyan/5 px-3 py-1.5 text-[10px] font-mono text-hud-cyan">
            <Bell className="h-3 w-3 shrink-0" />
            <div className="flex-1 flex flex-wrap gap-x-3 gap-y-0.5">
              {approachingAlerts.map((a) => (
                <span key={a.id} className="whitespace-nowrap">
                  {a.asset} → ${a.targetPrice.toLocaleString()}
                  {a.condition === "above" ? " ↑" : " ↓"}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* ============================================================= */}
        {/* HUD 3-Column Layout                                           */}
        {/* Desktop: [160px] [1fr] [155px]                                */}
        {/* Mobile: single column stack                                    */}
        {/* ============================================================= */}
        <div className="grid grid-cols-1 md:grid-cols-[160px_1fr_155px] gap-3">

          {/* LEFT COLUMN: System Status + Market Sentiment */}
          <div className="space-y-3 md:order-1 order-3">
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
            <MarketPulse data={sentimentData} />
            <RegimeDisplay
              regime={regime}
              metaUncertainty={status?.meta_unsicherheit ?? 0}
              ece={status?.ece ?? 0}
              oodScore={status?.ood_score ?? 0}
              loading={statusLoading}
            />
          </div>

          {/* CENTER COLUMN: Chart + Controls */}
          <div className="space-y-3 md:order-2 order-1">
            {/* Asset tabs + Status badges */}
            <HudPanel>
              <div className="p-2.5 space-y-3">
                {/* Asset Selector */}
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex flex-wrap gap-1 items-center">
                    {CHART_ASSETS.map((a, i) => (
                      <button
                        key={a.symbol}
                        onClick={() => { setSelectedAsset(i); setWsPrice(null); }}
                        className={`px-2 py-0.5 rounded text-[10px] font-mono font-medium transition-colors ${
                          selectedAsset === i
                            ? "bg-hud-cyan/15 text-hud-cyan border border-hud-cyan/30"
                            : "text-muted-foreground hover:text-hud-cyan hover:bg-hud-cyan/5"
                        }`}
                        suppressHydrationWarning
                      >
                        {a.symbol}
                      </button>
                    ))}
                    <button
                      onClick={saveFavorite}
                      className={`ml-0.5 p-0.5 rounded transition-colors ${
                        isCurrentFavorite ? "text-hud-amber" : "text-muted-foreground hover:text-hud-amber"
                      }`}
                      title={isCurrentFavorite ? "Current favorite" : "Set as favorite"}
                      suppressHydrationWarning
                    >
                      <Star className={`h-3 w-3 ${isCurrentFavorite ? "fill-hud-amber" : ""}`} />
                    </button>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-[8px] font-mono border-hud-border text-muted-foreground">
                      {TIMEFRAMES[timeframeIdx].label} / {TIMEFRAMES[timeframeIdx].strategyLabel}
                    </Badge>
                    <div className="flex items-center gap-1" suppressHydrationWarning>
                      <Zap className={`h-2.5 w-2.5 ${wsConnected ? "text-hud-green" : binanceConnected ? "text-hud-cyan" : "text-hud-amber"}`} />
                      <span className="text-[8px] font-mono text-muted-foreground" suppressHydrationWarning>
                        {wsConnected ? "WS" : binanceConnected ? "REST" : "Sim"}
                      </span>
                    </div>
                    <button
                      onClick={() => router.push("/charts")}
                      className="flex items-center gap-0.5 text-[9px] font-mono text-muted-foreground hover:text-hud-cyan transition-colors"
                    >
                      Expand <ArrowRight className="h-2.5 w-2.5" />
                    </button>
                  </div>
                </div>

                {/* Timeframe Slider */}
                <TimeframeSlider value={timeframeIdx} onChange={setTimeframeIdx} />

                {/* Strategy Control */}
                <div className="border-t border-hud-border/30 pt-1.5">
                  <StrategyControl
                    state={strategy.state}
                    backtestResult={strategy.backtestResult}
                    backtesting={strategy.backtesting}
                    selectStrategy={strategy.selectStrategy}
                    updateParam={strategy.updateParam}
                    addRule={strategy.addRule}
                    removeRule={strategy.removeRule}
                    executeBacktest={strategy.executeBacktest}
                    embedded
                  />
                </div>

                {/* Chart */}
                <div className="relative">
                  <AssetChart
                    key={`${asset.symbol}-${chartInterval}`}
                    symbol={asset.symbol}
                    name={asset.name}
                    basePrice={asset.basePrice}
                    livePrice={wsPrice ?? prices[asset.symbol]}
                    regime={regime}
                    height={380}
                    interval={chartInterval}
                    onPriceChange={handlePriceChange}
                    strategyOverlay={strategyOverlay}
                    jarvisTips={jarvisTipsCtx}
                  />
                  {/* Scan line overlay */}
                  <div className="hud-scan-line" />
                </div>
              </div>
            </HudPanel>

            {/* CoPilot Embed */}
            <CoPilotEmbed
              state={copilot.state}
              sendMessage={copilot.sendMessage}
              onExpand={() => setCopilotOpen(true)}
            />

            {/* Portfolio + Watchlist (below chart) */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
              <HudPanel title="Portfolio" scanLine>
                <div className="p-2.5">
                  <div className="grid grid-cols-2 gap-2">
                    <div className="rounded bg-hud-bg/60 border border-hud-border/30 p-2.5">
                      <div className="text-[9px] font-mono text-muted-foreground/60 mb-0.5">Total Value</div>
                      <div className="text-lg font-bold font-mono text-white">
                        ${totalValue.toLocaleString("en-US", { maximumFractionDigits: 0 })}
                      </div>
                    </div>
                    <div className="rounded bg-hud-bg/60 border border-hud-border/30 p-2.5">
                      <div className="text-[9px] font-mono text-muted-foreground/60 mb-0.5 flex items-center gap-1">
                        {totalPnl >= 0 ? <TrendingUp className="h-2.5 w-2.5 text-hud-green" /> : <TrendingDown className="h-2.5 w-2.5 text-hud-red" />}
                        Total P&L
                      </div>
                      <div className={`text-lg font-bold font-mono ${totalPnl >= 0 ? "text-hud-green" : "text-hud-red"}`}>
                        {totalPnl >= 0 ? "+" : ""}${Math.abs(totalPnl).toFixed(0)}
                      </div>
                    </div>
                    <div className="rounded bg-hud-bg/60 border border-hud-border/30 p-2.5">
                      <div className="text-[9px] font-mono text-muted-foreground/60 mb-0.5">Positions</div>
                      <div className="text-lg font-bold font-mono text-hud-cyan">{portfolio.positions.length}</div>
                    </div>
                    <div className="rounded bg-hud-bg/60 border border-hud-border/30 p-2.5">
                      <div className="text-[9px] font-mono text-muted-foreground/60 mb-0.5 flex items-center gap-1">
                        <MetricTooltip term="Drawdown">
                          <ShieldAlert className="h-2.5 w-2.5" />
                          Drawdown
                        </MetricTooltip>
                      </div>
                      <div className={`text-lg font-bold font-mono ${drawdown > 5 ? "text-hud-red" : drawdown > 0 ? "text-hud-amber" : "text-hud-green"}`}>
                        {drawdown.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                  {portfolio.closedTrades.length > 0 && (
                    <div className="mt-2 flex items-center gap-4 text-[9px] font-mono text-muted-foreground">
                      <MetricTooltip term="Win Rate">
                        <span>Win Rate: <span className={winRate >= 50 ? "text-hud-green" : "text-hud-red"}>{winRate.toFixed(0)}%</span></span>
                      </MetricTooltip>
                      <span>Trades: <span className="text-white">{portfolio.closedTrades.length}</span></span>
                    </div>
                  )}
                </div>
              </HudPanel>
              <div className="space-y-3">
                <Watchlist
                  prices={prices}
                  priceHistory={priceHistory}
                  signals={signals.map((s) => ({ asset: s.asset, direction: s.direction, confidence: s.confidence }))}
                />
                <ActivityFeed
                  closedTrades={portfolio.closedTrades.map((t) => ({ id: t.id, asset: t.asset, direction: t.direction, pnl: t.pnl, closedAt: t.closedAt }))}
                  openPositions={portfolio.positions.map((p) => ({ asset: p.asset, direction: p.direction, openedAt: p.openedAt }))}
                />
              </div>
            </div>

            {/* Status footer row */}
            <div className="flex items-center justify-end gap-3 text-[8px] font-mono text-muted-foreground/50" suppressHydrationWarning>
              {statusUpdated && <span suppressHydrationWarning>Status: {relativeTime(statusUpdated)}</span>}
              {metricsUpdated && <span suppressHydrationWarning>Metrics: {relativeTime(metricsUpdated)}</span>}
              {apiLatencyMs !== null && (
                <span className="flex items-center gap-0.5" suppressHydrationWarning>
                  <Activity className="h-2 w-2" /> {apiLatencyMs}ms
                </span>
              )}
              <button onClick={refreshAll} className="flex items-center gap-0.5 text-muted-foreground/50 hover:text-hud-cyan transition-colors" title="Refresh (R)">
                <RefreshCw className="h-2.5 w-2.5" /> Refresh
              </button>
            </div>
          </div>

          {/* RIGHT COLUMN: Top Signals + Signal Quality */}
          <div className="space-y-3 md:order-3 order-2">
            <TopSignalsHud
              signals={signals}
              portfolio={portfolio}
              acceptSignal={acceptSignal}
              loading={signalsLoading}
            />
            <SignalQuality
              signals={signals}
              metrics={metrics}
              accuracyByAsset={accuracyByAsset}
              backendOnline={backendOnline}
            />
            <QualityScoreCard metrics={metrics} loading={metricsLoading} />
          </div>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          <StatCard label="Predictions Today" value={status?.entscheidungs_count?.toString() ?? "0"} />
          <StatCard label="Model Calibration" value={metrics ? `${(metrics.calibration_component * 100).toFixed(1)}%` : "—"} />
          <StatCard label="Data Quality" value={metrics ? `${(metrics.data_quality_component * 100).toFixed(1)}%` : "—"} />
          <StatCard label="System Uptime" value="100%" />
        </div>
      </div>

      {/* JARVIS Co-Pilot */}
      <CoPilotTrigger onClick={() => setCopilotOpen(true)} />
      <CoPilotPanel
        open={copilotOpen}
        onClose={() => setCopilotOpen(false)}
        state={copilot.state}
        sendMessage={copilot.sendMessage}
        setRiskProfile={copilot.setRiskProfile}
        setLocale={copilot.setLocale}
        clearHistory={copilot.clearHistory}
      />
    </>
  );
}
