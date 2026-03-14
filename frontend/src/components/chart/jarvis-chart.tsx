// =============================================================================
// src/components/chart/jarvis-chart.tsx — JarvisChart (Screenshot-Accurate v3)
// =============================================================================

"use client";

import React, { useCallback, useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import { ChevronDown, Star } from "lucide-react";
import type { Signal } from "@/lib/types";

// ---------------------------------------------------------------------------
// Asset brand definitions — Fix #1: correct icons showing ticker text
// ---------------------------------------------------------------------------

const ASSET_BRANDS: Record<string, { color: string; icon: string; pair: string; rank: number; type: string; exchange: string }> = {
  BTC:  { color: "#f7931a", icon: "₿",   pair: "BTCUSD",  rank: 1,  type: "Crypto",      exchange: "Binance" },
  ETH:  { color: "#627eea", icon: "Ξ",   pair: "ETHUSD",  rank: 2,  type: "Crypto",      exchange: "Binance" },
  SOL:  { color: "#9945ff", icon: "SOL",  pair: "SOLUSD",  rank: 3,  type: "Crypto",      exchange: "Binance" },
  BNB:  { color: "#f3ba2f", icon: "BNB",  pair: "BNBUSD",  rank: 4,  type: "Crypto",      exchange: "Binance" },
  XRP:  { color: "#346aa9", icon: "XRP",  pair: "XRPUSD",  rank: 5,  type: "Crypto",      exchange: "Binance" },
  ADA:  { color: "#0d1e6f", icon: "ADA",  pair: "ADAUSD",  rank: 6,  type: "Crypto",      exchange: "Binance" },
  SPY:  { color: "#1565c0", icon: "SPY",  pair: "SPY",     rank: 1,  type: "Stocks",      exchange: "Yahoo" },
  AAPL: { color: "#555555", icon: "",    pair: "AAPL",    rank: 2,  type: "Stocks",      exchange: "Yahoo" },
  NVDA: { color: "#76b900", icon: "NVDA", pair: "NVDA",    rank: 3,  type: "Stocks",      exchange: "Yahoo" },
  TSLA: { color: "#e31937", icon: "TSLA", pair: "TSLA",    rank: 4,  type: "Stocks",      exchange: "Yahoo" },
  GLD:  { color: "#d4af37", icon: "Au",   pair: "GLD",     rank: 1,  type: "Commodities", exchange: "Yahoo" },
  OIL:  { color: "#37474f", icon: "OIL",  pair: "OIL",     rank: 2,  type: "Commodities", exchange: "Yahoo" },
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

const RANGE_PERF: Record<string, number> = {
  "1D": -0.02, "1W": 4.0, "1M": 5.8, "6M": -38.51,
  "YTD": -19.07, "1Y": -12.61, "5Y": 18.07, "ALL": 916,
};

const STRATEGY_OPTIONS = [
  "Combined", "Swing Trading", "Scalping", "Day Trading",
  "Trend Following", "Breakout", "Mean Reversion", "Custom",
];

// ---------------------------------------------------------------------------
// Fix #1: Asset Logo — shows ticker text on brand-color circle
// ---------------------------------------------------------------------------

function AssetLogo({ symbol, size = 56 }: { symbol: string; size?: number }) {
  const b = ASSET_BRANDS[symbol] ?? { color: "#4a9eff", icon: symbol, rank: 0 };
  const isLong = b.icon.length > 2;
  return (
    <div className="relative shrink-0">
      <div
        className="rounded-full flex items-center justify-center font-bold text-white select-none"
        style={{ width: size, height: size, backgroundColor: b.color, fontSize: isLong ? size * 0.22 : size * 0.38 }}
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
// Props
// ---------------------------------------------------------------------------

export type ChartType = "line" | "candle" | "bar";

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
  chartType: ChartType;
  onChartTypeChange: (t: ChartType) => void;
  onAssetChange: (symbol: string) => void;
  allAssets: { symbol: string; name: string; basePrice: number }[];
  prices: Record<string, number>;
  isFavorite: boolean;
  onSaveFavorite: () => void;
  children: React.ReactNode;
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export const JarvisChart = React.memo(function JarvisChart({
  selectedAsset, assetName, price, priceChange, priceChangePct,
  wsConnected, topSignal, selectedStrategy,
  timeframeIdx, onTimeframeChange, chartType, onChartTypeChange, onAssetChange,
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

      {/* ══ 1. ASSET HEADER ══ */}
      <div className="flex items-start gap-4 px-4 pt-4 pb-3">
        <AssetLogo symbol={selectedAsset} size={56} />

        <div className="flex-1 min-w-0">
          <h2 className="text-xl font-bold text-white leading-tight">{assetName}</h2>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-xs text-muted-foreground">{brand.pair} ·</span>
            <span className="flex items-center gap-1 text-xs text-muted-foreground border border-[#1a2030] rounded-full px-2 py-0.5">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: brand.color }} />
              {brand.exchange} <ChevronDown className="h-2.5 w-2.5" />
            </span>
            <div className="h-2.5 w-2.5 rounded-full bg-hud-green animate-pulse-live" />
          </div>
          <div className="flex items-baseline gap-3 mt-1">
            <span className="text-3xl font-bold text-white tracking-tight">
              ${price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
            <span className={cn("text-sm font-semibold", isPositive ? "text-hud-green" : "text-hud-red")}>
              {isPositive ? "+" : "-"}{Math.abs(priceChange).toFixed(2)}{" "}
              {isPositive ? "-" : "-"}{Math.abs(priceChangePct).toFixed(2)}%
            </span>
          </div>
          <div className="text-[10px] text-muted-foreground/60 mt-0.5">{dateStr}</div>
        </div>

        {/* Fix #5: AI SIGNAL — exact layout from screenshot */}
        <div className="text-right shrink-0 pt-0">
          <button onClick={onSaveFavorite} className="mb-1" suppressHydrationWarning>
            <Star className={cn("h-4 w-4", isFavorite ? "text-hud-amber fill-hud-amber" : "text-muted-foreground/20 hover:text-hud-amber")} />
          </button>
          <div className="text-[8px] tracking-[2px] uppercase" style={{ color: "#4a5270" }}>AI SIGNAL</div>
          {topSignal ? (
            <>
              <div className="text-[20px] font-semibold leading-tight" style={{ color: topSignal.direction === "LONG" ? "#4a9eff" : "#ff3d57" }}>
                {topSignal.direction}
              </div>
              <div className="text-[9px]" style={{ color: "#4a5270" }}>
                {(topSignal.confidence * 100).toFixed(0)}% Konfidenz
              </div>
              <div className="text-[8px]" style={{ color: "#f5a623" }}>
                {selectedStrategy}
              </div>
            </>
          ) : (
            <div className="text-[20px] font-semibold leading-tight" style={{ color: "#4a9eff" }}>NEUTRAL</div>
          )}
        </div>
      </div>

      {/* ══ 2. NAV TABS ══ */}
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

      {/* ══ TAB CONTENT ══ */}
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
                        <div className="w-5 h-5 rounded-full flex items-center justify-center text-[6px] font-bold text-white" style={{ backgroundColor: ab?.color ?? "#4a9eff" }}>{ab?.icon ?? a.symbol[0]}</div>
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
          {/* ══ Fix #2: SINGLE TOOLBAR ROW — all in one line ══ */}
          <div className="flex items-center gap-1.5 px-3 py-2 border-b border-[#1a2030] overflow-x-auto scrollbar-hide">
            {/* Price/MCap toggle */}
            <div className="flex rounded border border-[#1a2030] overflow-hidden shrink-0">
              <button onClick={() => setPriceMode("price")} className={cn("px-2 py-1 text-[9px]", priceMode === "price" ? "bg-[#1a2030] text-white" : "text-muted-foreground")}>
                Preis
              </button>
              <button onClick={() => setPriceMode("mcap")} className={cn("px-2 py-1 text-[9px]", priceMode === "mcap" ? "bg-[#1a2030] text-white" : "text-muted-foreground")}>
                Marktkapital.
              </button>
            </div>

            {/* Chart type switcher */}
            <div className="flex rounded border border-[#1a2030] overflow-hidden shrink-0">
              <button onClick={() => onChartTypeChange("line")} title="Linie" className={cn("px-1.5 py-1 text-[10px]", chartType === "line" ? "bg-[#1a2030] text-[#4a9eff]" : "text-muted-foreground hover:text-white")}>
                ~/
              </button>
              <button onClick={() => onChartTypeChange("candle")} title="Kerzen" className={cn("px-1.5 py-1 text-[10px]", chartType === "candle" ? "bg-[#1a2030] text-[#4a9eff]" : "text-muted-foreground hover:text-white")}>
                |||
              </button>
              <button onClick={() => onChartTypeChange("bar")} title="Bars" className={cn("px-1.5 py-1 text-[10px]", chartType === "bar" ? "bg-[#1a2030] text-[#4a9eff]" : "text-muted-foreground hover:text-white")}>
                ▤
              </button>
            </div>

            <div className="w-px h-4 bg-[#1a2030] shrink-0" />

            {/* Timeframes */}
            {TIMEFRAMES.map((tf, i) => (
              <button
                key={tf}
                onClick={() => onTimeframeChange(i)}
                className={cn(
                  "px-2 py-1 rounded border text-[9px] shrink-0 transition-colors",
                  timeframeIdx === i
                    ? "bg-[#1a2030] text-white border-[#2a3a52]"
                    : "text-muted-foreground border-transparent hover:text-white"
                )}
              >
                {tf}
              </button>
            ))}

            <div className="w-px h-4 bg-[#1a2030] shrink-0" />

            {/* Inline strategy dropdown */}
            <div className="relative shrink-0">
              <select
                defaultValue={selectedStrategy}
                className="appearance-none bg-[#0a0e14] border border-[#1a2030] rounded px-2 py-1 text-[9px] text-white pr-5 focus:outline-none"
              >
                {STRATEGY_OPTIONS.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-1 top-1/2 -translate-y-1/2 h-2.5 w-2.5 text-muted-foreground pointer-events-none" />
            </div>

            {/* Right: badges */}
            <div className="ml-auto flex items-center gap-1.5 shrink-0">
              <span className="text-[8px] tracking-[1px] text-muted-foreground uppercase">{selectedStrategy.toUpperCase()}</span>
              <span className={cn("text-[8px] tracking-[0.5px] border rounded px-1.5 py-0.5", wsConnected ? "text-[#4a9eff] border-[#4a9eff]/30" : "text-muted-foreground border-[#1a2030]")}>
                {wsConnected ? "SIM LIVE" : "OFFLINE"}
              </span>
            </div>
          </div>

          {/* ══ 4. CHART AREA — Fix #3: NO duplicate price line ══ */}
          <div className="relative" style={{ backgroundColor: "#08090d" }}>
            {children}
            {/* Watermark */}
            <div className="absolute bottom-2 right-3 text-[10px] tracking-[3px] text-white/[0.03] uppercase pointer-events-none select-none font-bold">
              JARVIS ENGINE
            </div>
            {/* Fix #4: Legend with pulse animations */}
            <div className="absolute bottom-2 left-3 flex items-center gap-3 pointer-events-none">
              <span className="flex items-center gap-1 text-[8px]"><span className="w-2.5 h-2.5 rounded-full bg-[#00e676]" style={{ animation: "pulse-green 2s infinite" }} />LONG</span>
              <span className="flex items-center gap-1 text-[8px]"><span className="w-2.5 h-2.5 rounded-full bg-[#ff3d57]" style={{ animation: "pulse-red 2s infinite" }} />SHORT</span>
              <span className="flex items-center gap-1 text-[8px]"><span className="w-2.5 h-2.5 rounded-full bg-[#4a9eff]" style={{ animation: "pulse-blue 2s infinite" }} />EXIT</span>
              <span className="flex items-center gap-1 text-[8px]"><span className="w-2.5 h-2.5 rounded-full bg-hud-amber" />TP/SL</span>
            </div>
          </div>

          {/* ══ 5. RANGE BAR ══ */}
          <div className="grid grid-cols-8 border-t border-[#1a2030]">
            {RANGE_TABS.map((r) => {
              const perf = RANGE_PERF[r.key] ?? 0;
              const pos = perf >= 0;
              return (
                <button key={r.key} onClick={() => setActiveRange(r.key)} className={cn("py-2 text-center transition-colors border-t-2", activeRange === r.key ? "border-[#4a9eff] bg-[#4a9eff]/5" : "border-transparent hover:bg-white/[0.02]")}>
                  <div className={cn("text-[9px]", activeRange === r.key ? "text-white" : "text-muted-foreground")}>{r.label}</div>
                  <div className={cn("text-[9px] font-bold", pos ? "text-hud-green" : "text-hud-red")}>{pos ? "+" : ""}{perf.toFixed(2)}%</div>
                </button>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
});
