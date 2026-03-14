// =============================================================================
// src/components/chart/jarvis-chart.tsx — JarvisChart Dashboard Component
//
// Complete chart area: Asset Header, Nav Tabs, Toolbar, Chart, Timeframe Bar,
// Markets Grid. Replaces the old center-column chart section.
// =============================================================================

"use client";

import React, { useCallback, useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Star, TrendingUp, TrendingDown, Zap } from "lucide-react";
import type { Signal } from "@/lib/types";

// ---------------------------------------------------------------------------
// Asset definitions with brand colors + SVG icon labels
// ---------------------------------------------------------------------------

const ASSET_BRANDS: Record<string, { color: string; label: string; pair: string; rank: number; type: string }> = {
  BTC: { color: "#f7931a", label: "B", pair: "BTCUSD", rank: 1, type: "Crypto" },
  ETH: { color: "#627eea", label: "Ξ", pair: "ETHUSD", rank: 2, type: "Crypto" },
  SOL: { color: "#9945ff", label: "S", pair: "SOLUSD", rank: 3, type: "Crypto" },
  BNB: { color: "#f3ba2f", label: "B", pair: "BNBUSD", rank: 4, type: "Crypto" },
  XRP: { color: "#346aa9", label: "X", pair: "XRPUSD", rank: 5, type: "Crypto" },
  ADA: { color: "#0d1e6f", label: "A", pair: "ADAUSD", rank: 6, type: "Crypto" },
  SPY: { color: "#1565c0", label: "S", pair: "SPY", rank: 1, type: "Stocks" },
  AAPL: { color: "#555555", label: "A", pair: "AAPL", rank: 2, type: "Stocks" },
  NVDA: { color: "#76b900", label: "N", pair: "NVDA", rank: 3, type: "Stocks" },
  TSLA: { color: "#e31937", label: "T", pair: "TSLA", rank: 4, type: "Stocks" },
  GLD: { color: "#d4af37", label: "Au", pair: "GLD", rank: 1, type: "Commodities" },
  OIL: { color: "#37474f", label: "O", pair: "OIL", rank: 2, type: "Commodities" },
};

const TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"] as const;
const RANGE_TABS = ["1D", "1W", "1M", "6M", "YTD", "1Y", "5Y", "ALL"] as const;
// Strategies available (used in toolbar badge display)

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function AssetLogo({ symbol, size = 44 }: { symbol: string; size?: number }) {
  const brand = ASSET_BRANDS[symbol] ?? { color: "#4a9eff", label: symbol[0], rank: 0 };
  return (
    <div className="relative shrink-0">
      <div
        className="rounded-full flex items-center justify-center font-bold text-white"
        style={{ width: size, height: size, backgroundColor: brand.color, fontSize: size * 0.4 }}
      >
        {brand.label}
      </div>
      {brand.rank > 0 && brand.rank <= 5 && (
        <div className="absolute -bottom-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-[#0d1117] border border-[#1a2030] text-[7px] font-bold text-white">
          #{brand.rank}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

interface JarvisChartProps {
  // Asset & price
  selectedAsset: string;
  assetName: string;
  price: number;
  priceChange: number;
  priceChangePct: number;
  wsConnected: boolean;
  // Signal
  topSignal: Signal | null;
  selectedStrategy: string;
  // Timeframe
  timeframeIdx: number;
  onTimeframeChange: (idx: number) => void;
  // Asset switching
  onAssetChange: (symbol: string) => void;
  allAssets: { symbol: string; name: string; basePrice: number }[];
  prices: Record<string, number>;
  // Favorite
  isFavorite: boolean;
  onSaveFavorite: () => void;
  // Chart render slot
  children: React.ReactNode;
}

export const JarvisChart = React.memo(function JarvisChart({
  selectedAsset, assetName, price, priceChange, priceChangePct,
  wsConnected, topSignal, selectedStrategy,
  timeframeIdx, onTimeframeChange, onAssetChange,
  allAssets, prices, isFavorite, onSaveFavorite,
  children,
}: JarvisChartProps) {
  const [activeTab, setActiveTab] = useState<string>("overview");
  const [activeRange, setActiveRange] = useState<string>("1M");
  const brand = ASSET_BRANDS[selectedAsset] ?? { color: "#4a9eff", label: "?", pair: selectedAsset, rank: 0, type: "Crypto" };
  const isPositive = priceChange >= 0;

  // Group assets for markets tab
  const assetGroups = useMemo(() => {
    const groups: Record<string, typeof allAssets> = { Crypto: [], Stocks: [], Commodities: [] };
    allAssets.forEach((a) => {
      const b = ASSET_BRANDS[a.symbol];
      const type = b?.type ?? "Crypto";
      if (!groups[type]) groups[type] = [];
      groups[type].push(a);
    });
    return groups;
  }, [allAssets]);

  const handleAssetClick = useCallback((symbol: string) => {
    onAssetChange(symbol);
    setActiveTab("overview");
  }, [onAssetChange]);

  return (
    <div className="rounded border border-hud-border bg-[#08090d] overflow-hidden font-mono">

      {/* ── 1. ASSET HEADER ── */}
      <div className="flex items-center gap-3 px-3 py-2.5 border-b border-[#141820]">
        <AssetLogo symbol={selectedAsset} size={44} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-white">{assetName}</span>
            <span className="text-[10px] text-muted-foreground">{brand.pair}</span>
            <div className="flex items-center gap-1">
              <div className="h-1.5 w-1.5 rounded-full bg-hud-green animate-pulse-live" />
              <span className="text-[8px] text-hud-green">LIVE</span>
            </div>
          </div>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-lg font-bold text-white">
              ${price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
            <span className={cn("text-xs font-bold flex items-center gap-0.5", isPositive ? "text-hud-green" : "text-hud-red")}>
              {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
              {isPositive ? "+" : ""}{priceChangePct.toFixed(2)}%
            </span>
          </div>
        </div>
        {/* Right: AI Signal */}
        <div className="flex items-center gap-2 shrink-0">
          {topSignal && (
            <div className="text-right">
              <div className={cn("text-[10px] font-bold", topSignal.direction === "LONG" ? "text-hud-green" : "text-hud-red")}>
                {topSignal.direction === "LONG" ? "▲ LONG" : "▼ SHORT"}
              </div>
              <div className="text-[9px] text-hud-cyan">{(topSignal.confidence * 100).toFixed(0)}% conf</div>
            </div>
          )}
          <button onClick={onSaveFavorite} className="p-1" suppressHydrationWarning>
            <Star className={cn("h-4 w-4", isFavorite ? "text-hud-amber fill-hud-amber" : "text-muted-foreground/40 hover:text-hud-amber")} />
          </button>
        </div>
      </div>

      {/* ── 2. NAV TABS ── */}
      <div className="flex border-b border-[#141820] overflow-x-auto scrollbar-hide">
        {[
          { id: "overview", label: "Übersicht" },
          { id: "technical", label: "Technisch" },
          { id: "markets", label: "Märkte" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "px-3 py-1.5 text-[10px] whitespace-nowrap transition-colors border-b-2",
              activeTab === tab.id
                ? "text-[#4a9eff] border-[#4a9eff]"
                : "text-muted-foreground border-transparent hover:text-white"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── TAB CONTENT ── */}
      {activeTab === "markets" ? (
        /* ── 6. MÄRKTE TAB ── */
        <div className="p-3 space-y-3">
          {Object.entries(assetGroups).map(([group, assets]) => (
            <div key={group}>
              <div className="text-[8px] tracking-[1.5px] text-muted-foreground/40 uppercase mb-1.5">{group}</div>
              <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-1.5">
                {assets.map((a) => {
                  const ab = ASSET_BRANDS[a.symbol];
                  const p = prices[a.symbol] ?? a.basePrice;
                  const isSelected = a.symbol === selectedAsset;
                  return (
                    <button
                      key={a.symbol}
                      onClick={() => handleAssetClick(a.symbol)}
                      className={cn(
                        "rounded border p-2 text-left transition-colors",
                        isSelected
                          ? "border-[#4a9eff]/40 bg-[#4a9eff]/5"
                          : "border-[#141820] hover:border-[#4a9eff]/20 bg-[#0d1017]"
                      )}
                    >
                      <div className="flex items-center gap-1.5 mb-1">
                        <div className="w-5 h-5 rounded-full flex items-center justify-center text-[8px] font-bold text-white" style={{ backgroundColor: ab?.color ?? "#4a9eff" }}>
                          {ab?.label ?? a.symbol[0]}
                        </div>
                        <span className="text-[9px] font-bold text-white">{a.symbol}</span>
                      </div>
                      <div className="text-[8px] text-muted-foreground">${p.toLocaleString("en-US", { maximumFractionDigits: p > 100 ? 0 : 2 })}</div>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <>
          {/* ── 3. CHART TOOLBAR ── */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 border-b border-[#141820] flex-wrap">
            {/* Timeframes */}
            {TIMEFRAMES.map((tf, i) => (
              <button
                key={tf}
                onClick={() => onTimeframeChange(i)}
                className={cn(
                  "px-1.5 py-0.5 rounded text-[9px] transition-colors",
                  timeframeIdx === i
                    ? "bg-[#4a9eff]/15 text-[#4a9eff] border border-[#4a9eff]/30"
                    : "text-muted-foreground hover:text-white"
                )}
              >
                {tf}
              </button>
            ))}
            <div className="w-px h-4 bg-[#141820] mx-1" />
            {/* Strategy badge */}
            <Badge className="text-[8px] bg-[#4a9eff]/10 text-[#4a9eff] border-[#4a9eff]/20">
              {selectedStrategy.toUpperCase()}
            </Badge>
            <Badge className="text-[8px] bg-hud-green/10 text-hud-green border-hud-green/20">
              SIM LIVE
            </Badge>
            {wsConnected && (
              <div className="ml-auto flex items-center gap-1">
                <Zap className="h-2.5 w-2.5 text-hud-green" />
                <span className="text-[8px] text-hud-green">WS</span>
              </div>
            )}
          </div>

          {/* ── 4. CHART AREA ── */}
          <div className="relative" style={{ backgroundColor: "#08090d" }}>
            {children}
            {/* Watermark */}
            <div className="absolute bottom-2 right-3 text-[9px] tracking-[2px] text-white/5 uppercase pointer-events-none select-none">
              JARVIS ENGINE
            </div>
            {/* Legend */}
            <div className="absolute bottom-2 left-3 flex items-center gap-2 pointer-events-none">
              <span className="flex items-center gap-1 text-[7px] text-hud-green/60"><span className="w-1.5 h-1.5 rounded-full bg-hud-green" />LONG</span>
              <span className="flex items-center gap-1 text-[7px] text-hud-red/60"><span className="w-1.5 h-1.5 rounded-full bg-hud-red" />SHORT</span>
              <span className="flex items-center gap-1 text-[7px] text-[#4a9eff]/60"><span className="w-1.5 h-1.5 rounded-full bg-[#4a9eff]" />EXIT</span>
            </div>
          </div>

          {/* ── 5. RANGE BAR ── */}
          <div className="flex items-center border-t border-[#141820]">
            {RANGE_TABS.map((r) => (
              <button
                key={r}
                onClick={() => setActiveRange(r)}
                className={cn(
                  "flex-1 py-1.5 text-[8px] text-center transition-colors border-t-2",
                  activeRange === r
                    ? "text-[#4a9eff] border-[#4a9eff] bg-[#4a9eff]/5"
                    : "text-muted-foreground border-transparent hover:text-white"
                )}
              >
                {r}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
});
