// =============================================================================
// src/components/chart/jarvis-chart.tsx — JarvisChart (Screenshot-Accurate)
// =============================================================================

"use client";

import React, { useCallback, useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import { ChevronDown, Star } from "lucide-react";
import type { Signal } from "@/lib/types";

// ---------------------------------------------------------------------------
// Asset brand definitions
// ---------------------------------------------------------------------------

const ASSET_BRANDS: Record<string, { color: string; icon: string; pair: string; rank: number; type: string; exchange: string }> = {
  BTC:  { color: "#f7931a", icon: "₿", pair: "BTCUSD",  rank: 1,  type: "Crypto",      exchange: "Binance" },
  ETH:  { color: "#627eea", icon: "Ξ", pair: "ETHUSD",  rank: 2,  type: "Crypto",      exchange: "Binance" },
  SOL:  { color: "#9945ff", icon: "S", pair: "SOLUSD",  rank: 3,  type: "Crypto",      exchange: "Binance" },
  BNB:  { color: "#f3ba2f", icon: "B", pair: "BNBUSD",  rank: 4,  type: "Crypto",      exchange: "Binance" },
  XRP:  { color: "#346aa9", icon: "X", pair: "XRPUSD",  rank: 5,  type: "Crypto",      exchange: "Binance" },
  ADA:  { color: "#0d1e6f", icon: "A", pair: "ADAUSD",  rank: 6,  type: "Crypto",      exchange: "Binance" },
  SPY:  { color: "#1565c0", icon: "S", pair: "SPY",     rank: 1,  type: "Stocks",      exchange: "Yahoo" },
  AAPL: { color: "#555555", icon: "", pair: "AAPL",    rank: 2,  type: "Stocks",      exchange: "Yahoo" },
  NVDA: { color: "#76b900", icon: "N", pair: "NVDA",    rank: 3,  type: "Stocks",      exchange: "Yahoo" },
  TSLA: { color: "#e31937", icon: "T", pair: "TSLA",    rank: 4,  type: "Stocks",      exchange: "Yahoo" },
  GLD:  { color: "#d4af37", icon: "Au",pair: "GLD",     rank: 1,  type: "Commodities", exchange: "Yahoo" },
  OIL:  { color: "#37474f", icon: "💧",pair: "OIL",     rank: 2,  type: "Commodities", exchange: "Yahoo" },
};

const TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"] as const;

const NAV_TABS = [
  { id: "overview", label: "Übersicht" },
  { id: "news", label: "Nachrichten" },
  { id: "community", label: "Community" },
  { id: "technical", label: "Technische Daten" },
  { id: "seasonal", label: "Saisonal" },
  { id: "markets", label: "Märkte" },
  { id: "etfs", label: "ETFs" },
];

const RANGE_TABS = [
  { key: "1D", label: "1 Tag" },
  { key: "1W", label: "1 Woche" },
  { key: "1M", label: "1 Monat" },
  { key: "6M", label: "6 Monate" },
  { key: "YTD", label: "Seit Jahresbeginn" },
  { key: "1Y", label: "1 Jahr" },
  { key: "5Y", label: "5 Jahre" },
  { key: "ALL", label: "Allzeit" },
];

// Simulated performance per range
const RANGE_PERF: Record<string, number> = {
  "1D": -0.02, "1W": 4.0, "1M": 5.8, "6M": -38.51,
  "YTD": -19.07, "1Y": -12.61, "5Y": 18.07, "ALL": 916,
};

const STRATEGY_OPTIONS = [
  "Combined", "Swing Trading", "Scalping", "Day Trading",
  "Trend Following", "Breakout", "Mean Reversion", "Custom",
];

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function AssetLogo({ symbol, size = 56 }: { symbol: string; size?: number }) {
  const b = ASSET_BRANDS[symbol] ?? { color: "#4a9eff", icon: symbol[0], rank: 0 };
  return (
    <div className="relative shrink-0">
      <div
        className="rounded-full flex items-center justify-center font-bold text-white select-none"
        style={{ width: size, height: size, backgroundColor: b.color, fontSize: size * 0.38 }}
      >
        {b.icon}
      </div>
      {b.rank > 0 && b.rank <= 6 && (
        <div className="absolute -bottom-1 -right-1 flex h-[18px] w-[18px] items-center justify-center rounded-full bg-[#0d1117] border-2 border-[#0d1117] text-[8px] font-bold text-white">
          #{b.rank}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

interface JarvisChartProps {
  selectedAsset: string;
  assetName: string;
  price: number;
  priceChange: number;
  priceChangePct: number;
  wsConnected: boolean;
  topSignal: Signal | null;
  selectedStrategy: string;
  timeframeIdx: number;
  onTimeframeChange: (idx: number) => void;
  onAssetChange: (symbol: string) => void;
  allAssets: { symbol: string; name: string; basePrice: number }[];
  prices: Record<string, number>;
  isFavorite: boolean;
  onSaveFavorite: () => void;
  children: React.ReactNode;
}

export const JarvisChart = React.memo(function JarvisChart({
  selectedAsset, assetName, price, priceChange, priceChangePct,
  wsConnected, topSignal, selectedStrategy,
  timeframeIdx, onTimeframeChange, onAssetChange,
  allAssets, prices, isFavorite, onSaveFavorite,
  children,
}: JarvisChartProps) {
  const [activeTab, setActiveTab] = useState("overview");
  const [activeRange, setActiveRange] = useState("1M");
  const [priceMode, setPriceMode] = useState<"price" | "mcap">("price");

  const brand = ASSET_BRANDS[selectedAsset] ?? { color: "#4a9eff", icon: "?", pair: selectedAsset, rank: 0, type: "Crypto", exchange: "?" };
  const isPositive = priceChange >= 0;

  const assetGroups = useMemo(() => {
    const groups: Record<string, typeof allAssets> = { Crypto: [], Stocks: [], Commodities: [] };
    allAssets.forEach((a) => {
      const t = ASSET_BRANDS[a.symbol]?.type ?? "Crypto";
      if (!groups[t]) groups[t] = [];
      groups[t].push(a);
    });
    return groups;
  }, [allAssets]);

  const handleAssetClick = useCallback((symbol: string) => {
    onAssetChange(symbol);
    setActiveTab("overview");
  }, [onAssetChange]);

  const now = new Date();
  const dateStr = `Ab heute, ${now.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" })} GMT+1`;

  return (
    <div className="rounded-lg border border-[#1a2030] bg-[#0d1117] overflow-hidden font-mono">

      {/* ══════════════════════════════════════════════════════════════════ */}
      {/* 1. ASSET HEADER                                                   */}
      {/* ══════════════════════════════════════════════════════════════════ */}
      <div className="flex items-start gap-4 px-4 pt-4 pb-3">
        <AssetLogo symbol={selectedAsset} size={56} />

        <div className="flex-1 min-w-0">
          {/* Row 1: Name */}
          <h2 className="text-xl font-bold text-white leading-tight">{assetName}</h2>

          {/* Row 2: Pair + Exchange + Live dot */}
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-xs text-muted-foreground">{brand.pair} ·</span>
            <span className="flex items-center gap-1 text-xs text-muted-foreground border border-[#1a2030] rounded-full px-2 py-0.5">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: brand.color }} />
              {brand.exchange} <ChevronDown className="h-2.5 w-2.5" />
            </span>
            <div className="flex items-center gap-1">
              <div className="h-2.5 w-2.5 rounded-full bg-hud-green animate-pulse-live" />
            </div>
          </div>

          {/* Row 3: Price + Change */}
          <div className="flex items-baseline gap-3 mt-1">
            <span className="text-3xl font-bold text-white tracking-tight">
              ${price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
            <span className={cn("text-sm font-semibold", isPositive ? "text-hud-green" : "text-hud-red")}>
              {isPositive ? "+" : ""}{Math.abs(priceChange).toFixed(2)}{" "}
              {isPositive ? "+" : ""}{priceChangePct.toFixed(2)}%
            </span>
          </div>

          {/* Row 4: Date */}
          <div className="text-[10px] text-muted-foreground/60 mt-0.5">{dateStr}</div>
        </div>

        {/* Right: AI SIGNAL */}
        <div className="text-right shrink-0 pt-1 relative">
          <button onClick={onSaveFavorite} className="absolute top-2 right-2" suppressHydrationWarning>
            <Star className={cn("h-4 w-4", isFavorite ? "text-hud-amber fill-hud-amber" : "text-muted-foreground/20 hover:text-hud-amber")} />
          </button>
          <div className="text-[9px] tracking-[2px] text-muted-foreground/50 uppercase">AI SIGNAL</div>
          {topSignal ? (
            <>
              <div className={cn("text-2xl font-bold leading-tight", topSignal.direction === "LONG" ? "text-hud-green" : "text-hud-red")}>
                {topSignal.direction}
              </div>
              <div className="text-[10px] text-muted-foreground">
                {(topSignal.confidence * 100).toFixed(0)}% Konfidenz
              </div>
              <div className="text-[9px] text-hud-cyan">{selectedStrategy}</div>
            </>
          ) : (
            <div className="text-sm text-muted-foreground/40">NEUTRAL</div>
          )}
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════════════════ */}
      {/* 2. NAV TABS                                                       */}
      {/* ══════════════════════════════════════════════════════════════════ */}
      <div className="flex border-b border-[#1a2030] overflow-x-auto scrollbar-hide px-1">
        {NAV_TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "px-3 py-2 text-[11px] whitespace-nowrap transition-colors border-b-2 -mb-px",
              activeTab === tab.id
                ? "text-[#4a9eff] border-[#4a9eff]"
                : "text-muted-foreground border-transparent hover:text-white"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ══════════════════════════════════════════════════════════════════ */}
      {/* TAB CONTENT                                                       */}
      {/* ══════════════════════════════════════════════════════════════════ */}
      {activeTab === "markets" ? (
        <div className="p-3 space-y-3">
          {Object.entries(assetGroups).map(([group, assets]) => (
            <div key={group}>
              <div className="text-[9px] tracking-[1.5px] text-muted-foreground/40 uppercase mb-1.5">{group}</div>
              <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-1.5">
                {assets.map((a) => {
                  const ab = ASSET_BRANDS[a.symbol];
                  const p = prices[a.symbol] ?? a.basePrice;
                  const sel = a.symbol === selectedAsset;
                  return (
                    <button key={a.symbol} onClick={() => handleAssetClick(a.symbol)} className={cn("rounded border p-2 text-left transition-all", sel ? "border-[#4a9eff]/40 bg-[#4a9eff]/5" : "border-[#1a2030] hover:border-[#4a9eff]/20 bg-[#0a0e14]")}>
                      <div className="flex items-center gap-1.5 mb-1">
                        <div className="w-5 h-5 rounded-full flex items-center justify-center text-[8px] font-bold text-white" style={{ backgroundColor: ab?.color ?? "#4a9eff" }}>{ab?.icon ?? a.symbol[0]}</div>
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
          {/* ── 3. TOOLBAR ROW 1: Price/MCap toggle + Timeframes ── */}
          <div className="flex items-center gap-2 px-4 py-2 border-b border-[#1a2030] flex-wrap">
            {/* Price / Marktkapitalisierung toggle */}
            <div className="flex rounded border border-[#1a2030] overflow-hidden">
              <button onClick={() => setPriceMode("price")} className={cn("px-2.5 py-1 text-[10px]", priceMode === "price" ? "bg-[#1a2030] text-white" : "text-muted-foreground hover:text-white")}>
                Preis
              </button>
              <button onClick={() => setPriceMode("mcap")} className={cn("px-2.5 py-1 text-[10px]", priceMode === "mcap" ? "bg-[#1a2030] text-white" : "text-muted-foreground hover:text-white")}>
                Marktkapital.
              </button>
            </div>

            <div className="w-px h-5 bg-[#1a2030]" />

            {/* Timeframes */}
            {TIMEFRAMES.map((tf, i) => (
              <button
                key={tf}
                onClick={() => onTimeframeChange(i)}
                className={cn(
                  "px-2.5 py-1 rounded border text-[10px] transition-colors",
                  timeframeIdx === i
                    ? "bg-[#1a2030] text-white border-[#2a3a52]"
                    : "text-muted-foreground border-transparent hover:text-white hover:border-[#1a2030]"
                )}
              >
                {tf}
              </button>
            ))}
          </div>

          {/* ── 3b. TOOLBAR ROW 2: Strategy dropdown ── */}
          <div className="px-4 py-2 border-b border-[#1a2030]">
            <div className="relative">
              <select
                value={selectedStrategy}
                className="w-full appearance-none bg-[#0a0e14] border border-[#1a2030] rounded px-3 py-2 text-[11px] text-white pr-8 focus:outline-none focus:border-[#4a9eff]/50"
                disabled
              >
                {STRATEGY_OPTIONS.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
            </div>
          </div>

          {/* ── 3c. COMBINED + SIM LIVE badges ── */}
          <div className="flex items-center justify-end gap-2 px-4 py-1.5 border-b border-[#1a2030]">
            <span className="text-[9px] tracking-[1.5px] text-muted-foreground uppercase">{selectedStrategy.toUpperCase()}</span>
            <span className={cn("text-[9px] tracking-[1px] border rounded px-2 py-0.5", wsConnected ? "text-[#4a9eff] border-[#4a9eff]/30" : "text-muted-foreground border-[#1a2030]")}>
              {wsConnected ? "SIM LIVE" : "OFFLINE"}
            </span>
          </div>

          {/* ── 4. CHART AREA ── */}
          <div className="relative" style={{ backgroundColor: "#08090d" }}>
            {children}
            {/* Watermark */}
            <div className="absolute bottom-2 right-3 text-[10px] tracking-[3px] text-white/[0.03] uppercase pointer-events-none select-none font-bold">
              JARVIS ENGINE
            </div>
            {/* Legend */}
            <div className="absolute bottom-2 left-3 flex items-center gap-3 pointer-events-none">
              <span className="flex items-center gap-1 text-[8px]"><span className="w-2 h-2 rounded-full bg-hud-green" />LONG</span>
              <span className="flex items-center gap-1 text-[8px]"><span className="w-2 h-2 rounded-full bg-hud-red" />SHORT</span>
              <span className="flex items-center gap-1 text-[8px]"><span className="w-2 h-2 rounded-full bg-[#4a9eff]" />EXIT</span>
              <span className="flex items-center gap-1 text-[8px]"><span className="w-2 h-2 rounded-full bg-hud-amber" />TP/SL</span>
            </div>
          </div>

          {/* ── 5. RANGE BAR (German labels + performance %) ── */}
          <div className="grid grid-cols-8 border-t border-[#1a2030]">
            {RANGE_TABS.map((r) => {
              const perf = RANGE_PERF[r.key] ?? 0;
              const perfPositive = perf >= 0;
              return (
                <button
                  key={r.key}
                  onClick={() => setActiveRange(r.key)}
                  className={cn(
                    "py-2 text-center transition-colors border-t-2",
                    activeRange === r.key
                      ? "border-[#4a9eff] bg-[#4a9eff]/5"
                      : "border-transparent hover:bg-white/[0.02]"
                  )}
                >
                  <div className={cn("text-[9px]", activeRange === r.key ? "text-white" : "text-muted-foreground")}>{r.label}</div>
                  <div className={cn("text-[9px] font-bold", perfPositive ? "text-hud-green" : "text-hud-red")}>
                    {perfPositive ? "+" : ""}{perf.toFixed(2)}%
                  </div>
                </button>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
});
