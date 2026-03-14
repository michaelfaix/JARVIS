// =============================================================================
// src/components/chart/jarvis-chart.tsx — JarvisChart v4 (Full Toolbar + OHLC)
// =============================================================================

"use client";

import React, { useCallback, useMemo, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import { Camera, ChevronDown, Star } from "lucide-react";
import type { Signal } from "@/lib/types";

// ---------------------------------------------------------------------------
// Constants
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
  { id: "overview", label: "Übersicht" }, { id: "news", label: "Nachrichten" },
  { id: "community", label: "Community" }, { id: "technical", label: "Technische Daten" },
  { id: "seasonal", label: "Saisonal" }, { id: "markets", label: "Märkte" }, { id: "etfs", label: "ETFs" },
];
const RANGE_TABS = [
  { key: "1D", label: "1 Tag" }, { key: "1W", label: "1 Woche" }, { key: "1M", label: "1 Monat" },
  { key: "6M", label: "6 Monate" }, { key: "YTD", label: "Seit Jahresbeginn" },
  { key: "1Y", label: "1 Jahr" }, { key: "5Y", label: "5 Jahre" }, { key: "ALL", label: "Allzeit" },
];
const RANGE_PERF: Record<string, number> = {
  "1D": -0.02, "1W": 4.0, "1M": 5.8, "6M": -38.51, "YTD": -19.07, "1Y": -12.61, "5Y": 18.07, "ALL": 916.51,
};
const STRATEGY_OPTIONS = ["Combined", "Swing Trading", "Scalping", "Day Trading", "Trend Following", "Breakout", "Mean Reversion", "Custom"];
const CHART_TYPE_LABELS: Record<string, string> = {
  line: "Linie", candle: "Candlestick", bar: "OHLC Bars",
  heikin: "Heikin Ashi", hollow: "Hollow Candles", linebreak: "Line Break", baseline: "Baseline",
};
const INDICATOR_GROUPS = [
  { title: "MOVING AVERAGES", items: ["EMA 9", "EMA 21", "EMA 50", "SMA 200"] },
  { title: "OSCILLATORS", items: ["RSI (14)", "MACD (12,26)", "Stochastic"] },
  { title: "VOLATILITY", items: ["Bollinger (20,2)", "ATR (14)", "VWAP"] },
];

// ---------------------------------------------------------------------------
// AssetLogo
// ---------------------------------------------------------------------------

function AssetLogo({ symbol, size = 56 }: { symbol: string; size?: number }) {
  const b = ASSET_BRANDS[symbol] ?? { color: "#4a9eff", icon: symbol, rank: 0 };
  const isLong = b.icon.length > 2;
  return (
    <div className="relative shrink-0">
      <div className="rounded-full flex items-center justify-center font-bold text-white select-none"
        style={{ width: size, height: size, backgroundColor: b.color, fontSize: isLong ? size * 0.22 : size * 0.38 }}>
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
// Types & Props
// ---------------------------------------------------------------------------

export type ChartType = "line" | "candle" | "bar" | "heikin" | "hollow" | "linebreak" | "baseline";

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
  activeIndicators?: string[];
  onToggleIndicator?: (name: string) => void;
  onScreenshot?: () => void;
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
  activeIndicators = [], onToggleIndicator, onScreenshot,
  children,
}: JarvisChartProps) {
  const [activeTab, setActiveTab] = useState("overview");
  const [activeRange, setActiveRange] = useState("1M");
  const [priceMode, setPriceMode] = useState<"price" | "mcap">("price");
  const [showExtTypes, setShowExtTypes] = useState(false);
  const [showIndicators, setShowIndicators] = useState(false);
  const extRef = useRef<HTMLDivElement>(null);
  const indRef = useRef<HTMLDivElement>(null);

  const brand = ASSET_BRANDS[selectedAsset] ?? { color: "#4a9eff", icon: "?", pair: selectedAsset, rank: 0, type: "Crypto", exchange: "?" };
  const isPositive = priceChange >= 0;
  const tf = TIMEFRAMES[timeframeIdx] ?? "1d";

  const assetGroups = useMemo(() => {
    const g: Record<string, typeof allAssets> = { Crypto: [], Stocks: [], Commodities: [] };
    allAssets.forEach((a) => { const t = ASSET_BRANDS[a.symbol]?.type ?? "Crypto"; if (!g[t]) g[t] = []; g[t].push(a); });
    return g;
  }, [allAssets]);

  const handleAssetClick = useCallback((symbol: string) => { onAssetChange(symbol); setActiveTab("overview"); }, [onAssetChange]);

  const now = new Date();
  const dateStr = `Ab heute, ${now.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" })} GMT+1`;

  return (
    <div className="rounded-lg border border-[#1a2030] bg-[#0d1117] overflow-hidden font-mono">

      {/* ════════════════════════════════════════════════════════════════ */}
      {/* 1. ASSET HEADER                                                */}
      {/* ════════════════════════════════════════════════════════════════ */}
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
            <span className="text-[32px] font-bold text-white tracking-tight leading-none">
              ${price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
            <span className={cn("text-sm font-semibold", isPositive ? "text-[#00e676]" : "text-[#ff3d57]")}>
              {isPositive ? "+" : ""}{priceChange.toFixed(2)}{" "}
              {isPositive ? "+" : ""}{priceChangePct.toFixed(2)}%
            </span>
          </div>
          <div className="text-[10px] text-muted-foreground/60 mt-0.5">{dateStr}</div>
        </div>
        <div className="text-right shrink-0 pt-0">
          <button onClick={onSaveFavorite} className="mb-1" suppressHydrationWarning>
            <Star className={cn("h-4 w-4", isFavorite ? "text-hud-amber fill-hud-amber" : "text-muted-foreground/20 hover:text-hud-amber")} />
          </button>
          <div className="text-[8px] tracking-[2px] uppercase" style={{ color: "#4a5270" }}>AI SIGNAL</div>
          {topSignal ? (
            <>
              <div className="text-[20px] font-semibold leading-tight" style={{ color: topSignal.direction === "LONG" ? "#4a9eff" : "#ff3d57" }}>{topSignal.direction}</div>
              <div className="text-[9px]" style={{ color: "#4a5270" }}>{(topSignal.confidence * 100).toFixed(0)}% Konfidenz</div>
              <div className="text-[8px]" style={{ color: "#f5a623" }}>{selectedStrategy}</div>
            </>
          ) : (
            <div className="text-[20px] font-semibold leading-tight" style={{ color: "#4a9eff" }}>NEUTRAL</div>
          )}
        </div>
      </div>

      {/* ════════════════════════════════════════════════════════════════ */}
      {/* 2. NAV TABS                                                    */}
      {/* ════════════════════════════════════════════════════════════════ */}
      <div className="flex border-b border-[#1a2030] overflow-x-auto scrollbar-hide px-1">
        {NAV_TABS.map((tab) => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={cn("px-3 py-2 text-[11px] whitespace-nowrap transition-colors border-b-2 -mb-px", activeTab === tab.id ? "text-[#4a9eff] border-[#4a9eff]" : "text-muted-foreground border-transparent hover:text-white")}>
            {tab.label}
          </button>
        ))}
      </div>

      {/* ════════════════════════════════════════════════════════════════ */}
      {/* TAB CONTENT                                                    */}
      {/* ════════════════════════════════════════════════════════════════ */}
      {activeTab === "markets" ? (
        <div className="p-3 space-y-3">
          {Object.entries(assetGroups).map(([group, assets]) => (
            <div key={group}>
              <div className="text-[9px] tracking-[1.5px] text-muted-foreground/40 uppercase mb-1.5">{group}</div>
              <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-1.5">
                {assets.map((a) => {
                  const ab = ASSET_BRANDS[a.symbol]; const p = prices[a.symbol] ?? a.basePrice; const sel = a.symbol === selectedAsset;
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
          {/* ══ UNIFIED TOOLBAR — one row, no scroll ══ */}
          <div
            className="relative flex items-center gap-1 px-3 py-1.5 border-b border-[#1e2335] bg-[#0d0f18]"
            style={{ flexWrap: "nowrap", overflow: "visible", zIndex: 100 }}
          >
            {/* Price/MCap */}
            <div className="flex rounded border border-[#1a2030] overflow-hidden shrink-0">
              <button onClick={() => setPriceMode("price")} className={cn("px-1.5 py-1 text-[9px] whitespace-nowrap", priceMode === "price" ? "bg-[#181c2a] text-white" : "text-[#4a5270]")}>Preis</button>
              <button onClick={() => setPriceMode("mcap")} className={cn("px-1.5 py-1 text-[9px] whitespace-nowrap", priceMode === "mcap" ? "bg-[#181c2a] text-white" : "text-[#4a5270]")}>Mkt.</button>
            </div>

            <div className="w-px h-4 bg-[#1e2335] shrink-0" />

            {/* Chart Types: 3 main + extended dropdown */}
            {(["line", "candle", "bar"] as const).map((t) => (
              <button key={t} onClick={() => onChartTypeChange(t)} title={CHART_TYPE_LABELS[t]}
                className={cn("w-[26px] h-[26px] rounded text-[10px] border shrink-0", chartType === t ? "bg-[#181c2a] border-[#4a9eff] text-[#4a9eff]" : "border-transparent text-[#4a5270] hover:bg-[#181c2a] hover:text-[#8892b0]")}>
                {t === "line" ? "〜" : t === "candle" ? "|||" : "▤"}
              </button>
            ))}
            <div className="relative shrink-0" ref={extRef}>
              <button onClick={() => { setShowExtTypes(!showExtTypes); setShowIndicators(false); }}
                className={cn("w-[26px] h-[26px] rounded text-[10px] border flex items-center justify-center shrink-0", ["heikin", "hollow", "linebreak", "baseline"].includes(chartType) ? "bg-[#181c2a] border-[#4a9eff] text-[#4a9eff]" : "border-transparent text-[#4a5270] hover:bg-[#181c2a]")}>
                ≋
              </button>
              {showExtTypes && (
                <div className="absolute top-8 left-0 z-[9999] bg-[#0d0f18] border border-[#1e2335] rounded-md p-2 shadow-2xl min-w-[160px]">
                  <div className="text-[8px] text-[#4a5270] tracking-[1px] uppercase mb-1">ERWEITERTE TYPEN</div>
                  {([["heikin", "≋ Heikin Ashi"], ["hollow", "⊡ Hollow Candles"], ["linebreak", "▭ Line Break"], ["baseline", "◨ Baseline"]] as const).map(([id, label]) => (
                    <button key={id} onClick={() => { onChartTypeChange(id as ChartType); setShowExtTypes(false); }}
                      className={cn("flex items-center gap-2 w-full px-2 py-1.5 rounded text-[10px]", chartType === id ? "text-[#4a9eff] bg-[#181c2a]" : "text-[#8892b0] hover:bg-[#181c2a] hover:text-white")}>
                      {label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="w-px h-4 bg-[#1e2335] shrink-0" />

            {/* Timeframes */}
            {TIMEFRAMES.map((tfv, i) => (
              <button key={tfv} onClick={() => onTimeframeChange(i)}
                className={cn("px-1.5 py-1 rounded text-[9px] shrink-0 whitespace-nowrap", timeframeIdx === i ? "bg-[#181c2a] text-white border border-[#4a9eff]" : "text-[#4a5270] border border-transparent hover:text-white")}>{tfv}</button>
            ))}

            <div className="w-px h-4 bg-[#1e2335] shrink-0" />

            {/* Strategy select */}
            <select defaultValue={selectedStrategy} className="appearance-none bg-[#181c2a] border border-[#1e2335] rounded px-1.5 py-1 text-[9px] text-[#8892b0] shrink-0 focus:outline-none max-w-[80px]">
              {STRATEGY_OPTIONS.map((s) => (<option key={s} value={s}>{s}</option>))}
            </select>

            <div className="w-px h-4 bg-[#1e2335] shrink-0" />

            {/* Indicators dropdown */}
            <div className="relative shrink-0" ref={indRef}>
              <button onClick={() => { setShowIndicators(!showIndicators); setShowExtTypes(false); }}
                className={cn("flex items-center gap-1 px-1.5 py-1 rounded text-[9px] shrink-0 whitespace-nowrap", activeIndicators.length > 0 ? "text-[#4a9eff] bg-[#4a9eff]/5 border border-[#4a9eff]/30" : "text-[#4a5270] border border-transparent hover:bg-[#181c2a]")}>
                📊{activeIndicators.length > 0 && <span className="text-[7px] bg-[#4a9eff] text-white rounded-full w-3.5 h-3.5 flex items-center justify-center">{activeIndicators.length}</span>}
              </button>
              {showIndicators && (
                <div className="absolute top-8 left-0 z-[9999] bg-[#0d0f18] border border-[#1e2335] rounded-md p-2 shadow-2xl min-w-[180px]">
                  {INDICATOR_GROUPS.map((group) => (
                    <div key={group.title}>
                      <div className="text-[8px] text-[#4a5270] tracking-[1px] uppercase mt-1 mb-1">{group.title}</div>
                      {group.items.map((ind) => {
                        const active = activeIndicators.includes(ind);
                        return (
                          <button key={ind} onClick={() => onToggleIndicator?.(ind)}
                            className="flex items-center gap-2 w-full px-2 py-1.5 rounded text-[10px] text-[#8892b0] hover:bg-[#181c2a] hover:text-white">
                            <div className={cn("w-3 h-3 rounded-sm border flex items-center justify-center text-[7px]", active ? "bg-[#4a9eff] border-[#4a9eff] text-white" : "border-[#1e2335]")}>{active ? "✓" : ""}</div>
                            {ind}
                          </button>
                        );
                      })}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Spacer */}
            <div className="flex-1" />

            {/* Right badges */}
            <span className="text-[8px] tracking-[1.5px] text-[#4a5270] uppercase shrink-0 whitespace-nowrap">{CHART_TYPE_LABELS[chartType]}</span>
            <span className={cn("text-[8px] border rounded px-1.5 py-0.5 shrink-0 whitespace-nowrap", wsConnected ? "text-[#4a9eff] border-[#4a9eff]/30 bg-[#4a9eff]/5" : "text-[#4a5270] border-[#1e2335]")}>{wsConnected ? "SIM LIVE" : "OFFLINE"}</span>
            <button onClick={onScreenshot} title="Screenshot" className="w-[26px] h-[26px] rounded text-[#4a5270] hover:bg-[#181c2a] hover:text-[#8892b0] shrink-0 flex items-center justify-center">
              <Camera className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* ══ OHLC SUB-HEADER (compact) ══ */}
          <div className="flex items-center gap-1.5 px-3 py-1 border-b border-[#181c2a] bg-[#08090d]" style={{ overflow: "visible" }}>
            <div className="w-3.5 h-3.5 rounded-full flex items-center justify-center text-[5px] font-bold text-white shrink-0" style={{ backgroundColor: brand.color }}>{brand.icon.length > 2 ? brand.icon[0] : brand.icon}</div>
            <span className="text-[9px] text-[#4a5270] shrink-0">{assetName} · {tf} · {CHART_TYPE_LABELS[chartType]}</span>
            <span className="text-[#1e2335] shrink-0">|</span>
            <span className="text-[8px] text-[#4a5270]">O</span><span className="text-[9px] text-[#8892b0]">{price.toFixed(2)}</span>
            <span className="text-[8px] text-[#4a5270]">H</span><span className="text-[9px] text-[#00e676]">{(price * 1.002).toFixed(2)}</span>
            <span className="text-[8px] text-[#4a5270]">L</span><span className="text-[9px] text-[#ff3d57]">{(price * 0.998).toFixed(2)}</span>
            <span className="text-[8px] text-[#4a5270]">C</span><span className={cn("text-[9px] font-bold", isPositive ? "text-[#00e676]" : "text-[#ff3d57]")}>{price.toFixed(2)}</span>
            <span className={cn("text-[9px]", isPositive ? "text-[#00e676]" : "text-[#ff3d57]")}>{isPositive ? "+" : ""}{priceChangePct.toFixed(2)}%</span>
            {activeIndicators.length > 0 && <span className="text-[#1e2335] shrink-0">|</span>}
            {activeIndicators.map((ind) => (
              <button key={ind} onClick={() => onToggleIndicator?.(ind)} className="text-[7px] px-1 py-0.5 rounded border border-[#4a9eff]/30 text-[#4a9eff] bg-[#4a9eff]/5 shrink-0">{ind} ×</button>
            ))}
          </div>

          {/* ══ CHART AREA ══ */}
          <div className="relative" style={{ backgroundColor: "#08090d" }}>
            {children}
            <div className="absolute bottom-2 right-3 text-[10px] tracking-[3px] text-white/[0.03] uppercase pointer-events-none select-none font-bold">JARVIS ENGINE</div>
            <div className="absolute bottom-2 left-3 flex items-center gap-3 pointer-events-none">
              <span className="flex items-center gap-1 text-[8px]"><span className="w-2.5 h-2.5 rounded-full bg-[#00e676]" style={{ animation: "pulse-green 2s infinite" }} />LONG</span>
              <span className="flex items-center gap-1 text-[8px]"><span className="w-2.5 h-2.5 rounded-full bg-[#ff3d57]" style={{ animation: "pulse-red 2s infinite" }} />SHORT</span>
              <span className="flex items-center gap-1 text-[8px]"><span className="w-2.5 h-2.5 rounded-full bg-[#4a9eff]" style={{ animation: "pulse-blue 2s infinite" }} />EXIT</span>
              <span className="flex items-center gap-1 text-[8px]"><span className="w-2.5 h-2.5 rounded-full bg-hud-amber" />TP/SL</span>
            </div>
          </div>

          {/* ══ RANGE BAR ══ */}
          <div className="grid grid-cols-8 border-t border-[#1a2030]">
            {RANGE_TABS.map((r) => { const perf = RANGE_PERF[r.key] ?? 0; const pos = perf >= 0; return (
              <button key={r.key} onClick={() => setActiveRange(r.key)} className={cn("py-2 text-center transition-colors border-t-2", activeRange === r.key ? "border-[#4a9eff] bg-[#4a9eff]/5" : "border-transparent hover:bg-white/[0.02]")}>
                <div className={cn("text-[9px]", activeRange === r.key ? "text-white" : "text-muted-foreground")}>{r.label}</div>
                <div className={cn("text-[9px] font-bold", pos ? "text-hud-green" : "text-hud-red")}>{pos ? "+" : ""}{perf.toFixed(2)}%</div>
              </button>
            ); })}
          </div>
        </>
      )}
    </div>
  );
});
