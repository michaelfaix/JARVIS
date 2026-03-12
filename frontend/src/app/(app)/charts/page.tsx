// =============================================================================
// src/app/(app)/charts/page.tsx — Dedicated Charts Page with Multi-Timeframe
//
// Live WebSocket prices flow into the chart (live candle) AND trigger
// JARVIS /predict signal refresh so signals stay in sync with price.
// =============================================================================

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AppHeader } from "@/components/layout/app-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AssetChart } from "@/components/chart/asset-chart";
import {
  IndicatorPanel,
  DEFAULT_INDICATORS,
  type IndicatorConfig,
} from "@/components/chart/indicator-panel";
import { DrawingToolbar } from "@/components/chart/drawing-toolbar";
import { useChartDrawings } from "@/hooks/use-chart-drawings";
import { usePrices } from "@/hooks/use-prices";
import { useSystemStatus } from "@/hooks/use-jarvis";
import { useSignals } from "@/hooks/use-signals";
import { DEFAULT_ASSETS } from "@/lib/constants";
import {
  CandlestickChart,
  Zap,
  TrendingUp,
  TrendingDown,
} from "lucide-react";
import { ApiOfflineBanner } from "@/components/ui/api-offline-banner";

const INTERVALS = [
  { value: "1m", label: "1m" },
  { value: "5m", label: "5m" },
  { value: "15m", label: "15m" },
  { value: "1h", label: "1H" },
  { value: "4h", label: "4H" },
  { value: "1d", label: "1D" },
  { value: "1w", label: "1W" },
] as const;

type Layout = "1x1" | "1x2" | "2x2";

interface ChartConfig {
  asset: number; // index into DEFAULT_ASSETS
  interval: string;
}

const DEFAULT_CHART_ASSETS = [0, 1, 2, 3]; // BTC, ETH, SOL, SPY

const LAYOUT_CHART_COUNT: Record<Layout, number> = {
  "1x1": 1,
  "1x2": 2,
  "2x2": 4,
};

const LAYOUT_HEIGHT: Record<Layout, number> = {
  "1x1": 500,
  "1x2": 400,
  "2x2": 300,
};

function getStoredLayout(): Layout {
  if (typeof window === "undefined") return "1x1";
  const stored = localStorage.getItem("jarvis-chart-layout");
  if (stored === "1x1" || stored === "1x2" || stored === "2x2") return stored;
  return "1x1";
}

function buildConfigs(count: number, existing: ChartConfig[]): ChartConfig[] {
  const configs: ChartConfig[] = [];
  for (let i = 0; i < count; i++) {
    if (i < existing.length) {
      configs.push(existing[i]);
    } else {
      configs.push({
        asset: DEFAULT_CHART_ASSETS[i] ?? 0,
        interval: "1d",
      });
    }
  }
  return configs;
}

// --- Layout toggle icons ---
function Icon1x1({ active }: { active: boolean }) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <rect
        x="1" y="1" width="14" height="14" rx="2"
        className={active ? "fill-blue-500/30 stroke-blue-400" : "fill-transparent stroke-muted-foreground"}
        strokeWidth="1.5"
      />
    </svg>
  );
}
function Icon1x2({ active }: { active: boolean }) {
  const cls = active ? "fill-blue-500/30 stroke-blue-400" : "fill-transparent stroke-muted-foreground";
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <rect x="1" y="1" width="6" height="14" rx="1.5" className={cls} strokeWidth="1.5" />
      <rect x="9" y="1" width="6" height="14" rx="1.5" className={cls} strokeWidth="1.5" />
    </svg>
  );
}
function Icon2x2({ active }: { active: boolean }) {
  const cls = active ? "fill-blue-500/30 stroke-blue-400" : "fill-transparent stroke-muted-foreground";
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <rect x="1" y="1" width="6" height="6" rx="1.5" className={cls} strokeWidth="1.5" />
      <rect x="9" y="1" width="6" height="6" rx="1.5" className={cls} strokeWidth="1.5" />
      <rect x="1" y="9" width="6" height="6" rx="1.5" className={cls} strokeWidth="1.5" />
      <rect x="9" y="9" width="6" height="6" rx="1.5" className={cls} strokeWidth="1.5" />
    </svg>
  );
}

const LAYOUT_ICONS: Record<Layout, React.FC<{ active: boolean }>> = {
  "1x1": Icon1x1,
  "1x2": Icon1x2,
  "2x2": Icon2x2,
};

// --- Compact per-chart header for multi-view ---
function CompactChartHeader({
  config,
  onAssetChange,
  onIntervalChange,
}: {
  config: ChartConfig;
  onAssetChange: (idx: number) => void;
  onIntervalChange: (interval: string) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-2 pb-2 flex-wrap">
      <div className="flex items-center gap-0.5 flex-wrap">
        {DEFAULT_ASSETS.map((a, i) => (
          <button
            key={a.symbol}
            onClick={() => onAssetChange(i)}
            className={`px-2 py-0.5 rounded text-[10px] font-medium transition-colors ${
              config.asset === i
                ? "bg-blue-600/20 text-blue-400"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            }`}
          >
            {a.symbol}
          </button>
        ))}
      </div>
      <div className="flex items-center gap-0.5 rounded-md border border-border/50 p-0.5">
        {INTERVALS.map((tf) => (
          <button
            key={tf.value}
            onClick={() => onIntervalChange(tf.value)}
            className={`px-1.5 py-0.5 rounded text-[9px] font-medium transition-colors ${
              config.interval === tf.value
                ? "bg-blue-600/20 text-blue-400"
                : "text-muted-foreground hover:text-white"
            }`}
          >
            {tf.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function ChartsPage() {
  const { prices, wsConnected, binanceConnected } = usePrices(5000);
  const { regime, error: statusError } = useSystemStatus(5000);
  const { signals, error: signalsError, refresh: refreshSignals } = useSignals(regime, 10000);

  // Layout state
  const [layout, setLayout] = useState<Layout>("1x1");
  const [chartConfigs, setChartConfigs] = useState<ChartConfig[]>([
    { asset: 0, interval: "1d" },
  ]);

  // Hydrate layout from localStorage on mount
  useEffect(() => {
    const stored = getStoredLayout();
    const count = LAYOUT_CHART_COUNT[stored];
    setLayout(stored);
    setChartConfigs((prev) => buildConfigs(count, prev));
  }, []);

  const handleLayoutChange = useCallback((newLayout: Layout) => {
    setLayout(newLayout);
    localStorage.setItem("jarvis-chart-layout", newLayout);
    const count = LAYOUT_CHART_COUNT[newLayout];
    setChartConfigs((prev) => buildConfigs(count, prev));
  }, []);

  const updateChartConfig = useCallback(
    (index: number, patch: Partial<ChartConfig>) => {
      setChartConfigs((prev) =>
        prev.map((c, i) => (i === index ? { ...c, ...patch } : c))
      );
    },
    []
  );

  // --- Single-chart (1x1) state: keeps existing behavior ---
  const singleConfig = chartConfigs[0] ?? { asset: 0, interval: "1d" };
  const selectedAsset = singleConfig.asset;
  const chartInterval = singleConfig.interval;

  const [indicators, setIndicators] = useState<IndicatorConfig>({
    ...DEFAULT_INDICATORS,
  });

  const {
    drawings,
    activeTool,
    setActiveTool,
    addDrawing,
    undoLast,
    clearAll,
  } = useChartDrawings(DEFAULT_ASSETS[selectedAsset].symbol);

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

  const isSingle = layout === "1x1";

  return (
    <>
      <AppHeader title="Charts" subtitle="Technical Analysis" />
      <div className="p-3 sm:p-4 md:p-6 space-y-3 md:space-y-4">
        {(statusError || signalsError) && <ApiOfflineBanner />}
        {/* Controls Bar */}
        <Card className="bg-card/50 border-border/50">
          <CardContent className="py-3 px-4">
            <div className="flex items-center justify-between flex-wrap gap-3">
              {/* Asset selector — only for single layout */}
              {isSingle ? (
                <div className="flex items-center gap-1 flex-wrap">
                  {DEFAULT_ASSETS.map((a, i) => (
                    <button
                      key={a.symbol}
                      onClick={() => {
                        updateChartConfig(0, { asset: i });
                        setWsPrice(null);
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
              ) : (
                <div className="text-xs text-muted-foreground">
                  Multi-chart: use per-chart controls below
                </div>
              )}

              {/* Timeframe + Layout + Status */}
              <div className="flex items-center gap-3">
                {/* Interval selector — only for single layout */}
                {isSingle && (
                  <div className="flex items-center gap-0.5 rounded-lg border border-border/50 p-0.5">
                    {INTERVALS.map((tf) => (
                      <button
                        key={tf.value}
                        onClick={() => {
                          updateChartConfig(0, { interval: tf.value });
                          setWsPrice(null);
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
                )}

                {/* Indicator selector — only for single layout */}
                {isSingle && (
                  <IndicatorPanel
                    value={indicators}
                    onChange={setIndicators}
                  />
                )}

                {/* Layout toggle */}
                <div className="flex items-center gap-0.5 rounded-lg border border-border/50 p-0.5">
                  {(["1x1", "1x2", "2x2"] as Layout[]).map((l) => {
                    const Icon = LAYOUT_ICONS[l];
                    const isActive = layout === l;
                    return (
                      <button
                        key={l}
                        onClick={() => handleLayoutChange(l)}
                        className={`p-1.5 rounded-md transition-colors ${
                          isActive
                            ? "bg-blue-600/20"
                            : "hover:bg-muted"
                        }`}
                        title={`${l} layout`}
                      >
                        <Icon active={isActive} />
                      </button>
                    );
                  })}
                </div>

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

        {/* Asset Info Bar — only for single layout */}
        {isSingle && (
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
        )}

        {/* Drawing Toolbar — only for single layout */}
        {isSingle && (
          <DrawingToolbar
            activeTool={activeTool}
            onToolChange={setActiveTool}
            onUndo={undoLast}
            onClearAll={clearAll}
            drawingCount={drawings.length}
          />
        )}

        {/* Chart Area */}
        {isSingle ? (
          /* Single Chart — key forces full remount on asset/interval change */
          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4">
              <AssetChart
                key={`${asset.symbol}-${chartInterval}`}
                symbol={asset.symbol}
                name={asset.name}
                basePrice={asset.price}
                livePrice={currentPrice}
                regime={regime}
                height={LAYOUT_HEIGHT["1x1"]}
                interval={chartInterval}
                onPriceChange={handlePriceChange}
                indicators={indicators}
                drawings={drawings}
                activeTool={activeTool}
                onDrawingComplete={addDrawing}
              />
            </CardContent>
          </Card>
        ) : (
          /* Multi-Chart Grid */
          <div className="grid grid-cols-2 gap-2">
            {chartConfigs.map((cfg, idx) => {
              const a = DEFAULT_ASSETS[cfg.asset];
              return (
                <Card key={idx} className="bg-card/50 border-border/50">
                  <CardContent className="pt-3 pb-2 px-3">
                    <CompactChartHeader
                      config={cfg}
                      onAssetChange={(assetIdx) =>
                        updateChartConfig(idx, { asset: assetIdx })
                      }
                      onIntervalChange={(interval) =>
                        updateChartConfig(idx, { interval })
                      }
                    />
                    <AssetChart
                      key={`${a.symbol}-${cfg.interval}`}
                      symbol={a.symbol}
                      name={a.name}
                      basePrice={a.price}
                      regime={regime}
                      height={LAYOUT_HEIGHT[layout]}
                      interval={cfg.interval}
                    />
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}

        {/* Signal Details — only for single layout */}
        {isSingle && signal && (
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
