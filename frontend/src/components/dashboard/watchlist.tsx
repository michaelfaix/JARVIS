// =============================================================================
// src/components/dashboard/watchlist.tsx — Asset watchlist with live prices
// =============================================================================

"use client";

import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { DEFAULT_ASSETS } from "@/lib/constants";
import {
  Star,
  TrendingUp,
  TrendingDown,
  Minus,
  Plus,
  X,
} from "lucide-react";

const STORAGE_KEY = "jarvis-watchlist";

function loadWatchlist(): string[] {
  if (typeof window === "undefined") return ["BTC", "ETH", "SOL"];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : ["BTC", "ETH", "SOL"];
  } catch {
    return ["BTC", "ETH", "SOL"];
  }
}

interface WatchlistProps {
  prices: Record<string, number>;
  signals?: { asset: string; direction: "LONG" | "SHORT"; confidence: number }[];
  priceHistory?: Record<string, number[]>;
}

function Sparkline({ data, color }: { data: number[]; color: string }) {
  if (data.length < 2) return null;
  const w = 60;
  const h = 20;
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
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function Watchlist({ prices, signals = [], priceHistory }: WatchlistProps) {
  const [watchlist, setWatchlist] = useState<string[]>(loadWatchlist);
  const [prevPrices, setPrevPrices] = useState<Record<string, number>>({});
  const [editing, setEditing] = useState(false);

  // Track price changes for flash effect
  useEffect(() => {
    setPrevPrices((prev) => {
      const next = { ...prev };
      for (const symbol of watchlist) {
        if (prices[symbol] !== undefined) {
          next[symbol] = prev[symbol] ?? prices[symbol];
        }
      }
      return next;
    });
    // Delayed update so we can show the diff
    const timer = setTimeout(() => {
      setPrevPrices({ ...prices });
    }, 1500);
    return () => clearTimeout(timer);
  }, [prices, watchlist]);

  const persist = useCallback((list: string[]) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
    } catch {
      // storage full or unavailable
    }
  }, []);

  const addAsset = useCallback(
    (symbol: string) => {
      setWatchlist((prev) => {
        if (prev.includes(symbol)) return prev;
        const next = [...prev, symbol];
        persist(next);
        return next;
      });
    },
    [persist]
  );

  const removeAsset = useCallback(
    (symbol: string) => {
      setWatchlist((prev) => {
        const next = prev.filter((s) => s !== symbol);
        persist(next);
        return next;
      });
    },
    [persist]
  );

  const signalMap = new Map(signals.map((s) => [s.asset, s]));
  const availableToAdd = DEFAULT_ASSETS.filter(
    (a) => !watchlist.includes(a.symbol)
  );

  return (
    <Card className="bg-card/50 border-border/50">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          <Star className="h-4 w-4" />
          Watchlist
          <button
            onClick={() => setEditing((p) => !p)}
            className="ml-auto text-[10px] text-muted-foreground hover:text-white transition-colors px-2 py-0.5 rounded border border-border/50"
          >
            {editing ? "Done" : "Edit"}
          </button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-1">
        {watchlist.map((symbol) => {
          const asset = DEFAULT_ASSETS.find((a) => a.symbol === symbol);
          const price = prices[symbol] ?? asset?.price ?? 0;
          const prev = prevPrices[symbol] ?? price;
          const change = price - prev;
          const changePct = prev > 0 ? (change / prev) * 100 : 0;
          const signal = signalMap.get(symbol);

          return (
            <div
              key={symbol}
              className="flex items-center gap-3 rounded-lg bg-background/50 px-3 py-2"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-white text-sm">
                    {symbol}
                  </span>
                  <span className="text-[10px] text-muted-foreground hidden sm:inline">
                    {asset?.name}
                  </span>
                  {signal && (
                    <Badge
                      className={`text-[9px] px-1 py-0 ${
                        signal.direction === "LONG"
                          ? "bg-green-500/20 text-green-400 border-green-500/30"
                          : "bg-red-500/20 text-red-400 border-red-500/30"
                      }`}
                    >
                      {signal.direction}
                    </Badge>
                  )}
                </div>
              </div>
              {priceHistory?.[symbol] && priceHistory[symbol].length >= 2 && (
                <Sparkline
                  data={priceHistory[symbol]}
                  color={
                    priceHistory[symbol][priceHistory[symbol].length - 1] >
                    priceHistory[symbol][0]
                      ? "#4ade80"
                      : priceHistory[symbol][priceHistory[symbol].length - 1] <
                        priceHistory[symbol][0]
                      ? "#f87171"
                      : "#6b7280"
                  }
                />
              )}
              <div className="text-right">
                <div className="text-sm font-mono text-white">
                  $
                  {price.toLocaleString("en-US", {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </div>
                <div
                  className={`text-[10px] font-mono flex items-center justify-end gap-0.5 ${
                    change > 0
                      ? "text-green-400"
                      : change < 0
                      ? "text-red-400"
                      : "text-muted-foreground"
                  }`}
                >
                  {change > 0 ? (
                    <TrendingUp className="h-2.5 w-2.5" />
                  ) : change < 0 ? (
                    <TrendingDown className="h-2.5 w-2.5" />
                  ) : (
                    <Minus className="h-2.5 w-2.5" />
                  )}
                  {Math.abs(changePct).toFixed(2)}%
                </div>
              </div>
              {editing && (
                <button
                  onClick={() => removeAsset(symbol)}
                  className="text-muted-foreground hover:text-red-400 transition-colors p-0.5"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          );
        })}

        {/* Add assets in edit mode */}
        {editing && availableToAdd.length > 0 && (
          <div className="pt-2 flex flex-wrap gap-1.5">
            {availableToAdd.map((a) => (
              <button
                key={a.symbol}
                onClick={() => addAsset(a.symbol)}
                className="flex items-center gap-1 rounded-md border border-border/50 px-2 py-1 text-[10px] text-muted-foreground hover:text-white hover:border-blue-500/50 transition-colors"
              >
                <Plus className="h-2.5 w-2.5" />
                {a.symbol}
              </button>
            ))}
          </div>
        )}

        {watchlist.length === 0 && (
          <div className="text-xs text-muted-foreground text-center py-4">
            Click Edit to add assets to your watchlist
          </div>
        )}
      </CardContent>
    </Card>
  );
}
