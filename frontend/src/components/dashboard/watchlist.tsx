// =============================================================================
// src/components/dashboard/watchlist.tsx — Watchlist (HUD)
// =============================================================================

"use client";

import { useCallback, useEffect, useState } from "react";
import { HudPanel } from "@/components/ui/hud-panel";
import { Badge } from "@/components/ui/badge";
import { DEFAULT_ASSETS } from "@/lib/constants";
import { TrendingUp, TrendingDown, Minus, Plus, X } from "lucide-react";

const STORAGE_KEY = "jarvis-watchlist";
const DEFAULT_WATCHLIST = ["BTC", "ETH", "SOL", "AAPL", "NVDA"];

interface WatchlistProps {
  prices: Record<string, number>;
  signals?: { asset: string; direction: "LONG" | "SHORT"; confidence: number }[];
  priceHistory?: Record<string, number[]>;
}

function Sparkline({ data, color }: { data: number[]; color: string }) {
  if (data.length < 2) return null;
  const w = 50;
  const h = 16;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const points = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * w;
      const y = h - ((v - min) / range) * h;
      return `${x},${y}`;
    })
    .join(" ");
  return (
    <svg width={w} height={h} className="shrink-0">
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function Watchlist({ prices, signals = [], priceHistory }: WatchlistProps) {
  const [watchlist, setWatchlist] = useState<string[]>(DEFAULT_WATCHLIST);
  const [prevPrices, setPrevPrices] = useState<Record<string, number>>({});
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed) && parsed.length > 0) setWatchlist(parsed);
      }
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    setPrevPrices((prev) => {
      const next = { ...prev };
      for (const symbol of watchlist) {
        if (prices[symbol] !== undefined) next[symbol] = prev[symbol] ?? prices[symbol];
      }
      return next;
    });
    const timer = setTimeout(() => setPrevPrices({ ...prices }), 1500);
    return () => clearTimeout(timer);
  }, [prices, watchlist]);

  const persist = useCallback((list: string[]) => {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(list)); } catch { /* */ }
  }, []);

  const addAsset = useCallback((symbol: string) => {
    setWatchlist((prev) => {
      if (prev.includes(symbol)) return prev;
      const next = [...prev, symbol];
      persist(next);
      return next;
    });
  }, [persist]);

  const removeAsset = useCallback((symbol: string) => {
    setWatchlist((prev) => {
      const next = prev.filter((s) => s !== symbol);
      persist(next);
      return next;
    });
  }, [persist]);

  const signalMap = new Map(signals.map((s) => [s.asset, s]));
  const availableToAdd = DEFAULT_ASSETS.filter((a) => !watchlist.includes(a.symbol));

  return (
    <HudPanel title="Watchlist">
      <div className="p-2">
        <div className="flex items-center justify-end mb-1.5">
          <button
            onClick={() => setEditing((p) => !p)}
            className="text-[8px] font-mono text-muted-foreground hover:text-hud-cyan transition-colors px-1.5 py-0.5 rounded border border-hud-border/50"
            suppressHydrationWarning
          >
            {editing ? "Done" : "Edit"}
          </button>
        </div>

        <div className="space-y-0.5">
          {watchlist.map((symbol) => {
            const asset = DEFAULT_ASSETS.find((a) => a.symbol === symbol);
            const price = prices[symbol] ?? asset?.price ?? 0;
            const prev = prevPrices[symbol] ?? price;
            const change = price - prev;
            const changePct = prev > 0 ? (change / prev) * 100 : 0;
            const signal = signalMap.get(symbol);

            return (
              <div key={symbol} className="flex items-center gap-2 rounded bg-hud-bg/40 px-2 py-1.5">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="font-mono text-[10px] font-bold text-white">{symbol}</span>
                    {signal && (
                      <Badge className={`text-[7px] px-0.5 py-0 font-mono ${signal.direction === "LONG" ? "bg-hud-green/20 text-hud-green border-hud-green/30" : "bg-hud-red/20 text-hud-red border-hud-red/30"}`}>
                        {signal.direction}
                      </Badge>
                    )}
                  </div>
                </div>
                {priceHistory?.[symbol] && priceHistory[symbol].length >= 2 && (
                  <Sparkline
                    data={priceHistory[symbol]}
                    color={priceHistory[symbol][priceHistory[symbol].length - 1] > priceHistory[symbol][0] ? "#00e5a0" : priceHistory[symbol][priceHistory[symbol].length - 1] < priceHistory[symbol][0] ? "#ff4466" : "#6b7280"}
                  />
                )}
                <div className="text-right">
                  <div className="text-[10px] font-mono text-white">
                    ${price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                  <div className={`text-[8px] font-mono flex items-center justify-end gap-0.5 ${change > 0 ? "text-hud-green" : change < 0 ? "text-hud-red" : "text-muted-foreground"}`}>
                    {change > 0 ? <TrendingUp className="h-2 w-2" /> : change < 0 ? <TrendingDown className="h-2 w-2" /> : <Minus className="h-2 w-2" />}
                    {Math.abs(changePct).toFixed(2)}%
                  </div>
                </div>
                {editing && (
                  <button onClick={() => removeAsset(symbol)} className="text-muted-foreground hover:text-hud-red transition-colors p-0.5">
                    <X className="h-3 w-3" />
                  </button>
                )}
              </div>
            );
          })}
        </div>

        {editing && availableToAdd.length > 0 && (
          <div className="pt-1.5 flex flex-wrap gap-1">
            {availableToAdd.map((a) => (
              <button key={a.symbol} onClick={() => addAsset(a.symbol)} className="flex items-center gap-0.5 rounded border border-hud-border/50 px-1.5 py-0.5 text-[8px] font-mono text-muted-foreground hover:text-hud-cyan hover:border-hud-cyan/30 transition-colors">
                <Plus className="h-2 w-2" /> {a.symbol}
              </button>
            ))}
          </div>
        )}

        {watchlist.length === 0 && (
          <div className="text-[10px] font-mono text-muted-foreground text-center py-4">
            Click Edit to add assets
          </div>
        )}
      </div>
    </HudPanel>
  );
}
