// =============================================================================
// src/hooks/use-prices.ts — Live prices from Binance public API
//
// Uses Binance REST API (no API key required) for crypto pairs.
// Non-crypto assets use synthetic prices with small random walk.
// =============================================================================

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { DEFAULT_ASSETS } from "@/lib/constants";

// Binance symbol mapping for crypto assets
const BINANCE_SYMBOLS: Record<string, string> = {
  BTC: "BTCUSDT",
  ETH: "ETHUSDT",
  SOL: "SOLUSDT",
};

// Fallback base prices for non-crypto assets
const FALLBACK_BASE: Record<string, number> = {};
for (const a of DEFAULT_ASSETS) {
  if (!(a.symbol in BINANCE_SYMBOLS)) {
    FALLBACK_BASE[a.symbol] = a.price;
  }
}

interface BinanceTickerResponse {
  symbol: string;
  price: string;
}

async function fetchBinancePrices(): Promise<Record<string, number>> {
  const symbols = Object.values(BINANCE_SYMBOLS);
  const qs = symbols.map((s) => `"${s}"`).join(",");
  const url = `https://api.binance.com/api/v3/ticker/price?symbols=[${qs}]`;

  const res = await fetch(url);
  if (!res.ok) throw new Error(`Binance API ${res.status}`);
  const data: BinanceTickerResponse[] = await res.json();

  const prices: Record<string, number> = {};
  // Reverse-map: BTCUSDT -> BTC
  for (const [symbol, binanceSymbol] of Object.entries(BINANCE_SYMBOLS)) {
    const ticker = data.find((d) => d.symbol === binanceSymbol);
    if (ticker) {
      prices[symbol] = parseFloat(ticker.price);
    }
  }
  return prices;
}

// Deterministic-ish walk for non-crypto (uses Date.now for tiny drift)
function syntheticPrices(
  prev: Record<string, number>
): Record<string, number> {
  const prices: Record<string, number> = {};
  for (const [symbol, base] of Object.entries(FALLBACK_BASE)) {
    const current = prev[symbol] ?? base;
    // Small random walk: ±0.3% per tick
    const seed = (Date.now() / 1000) * symbol.charCodeAt(0);
    const drift = (Math.sin(seed) * 0.003) * current;
    prices[symbol] = parseFloat((current + drift).toFixed(2));
  }
  return prices;
}

export function usePrices(intervalMs: number = 5000) {
  const [prices, setPrices] = useState<Record<string, number>>(() => {
    const initial: Record<string, number> = {};
    for (const a of DEFAULT_ASSETS) {
      initial[a.symbol] = a.price;
    }
    return initial;
  });
  const [binanceConnected, setBinanceConnected] = useState(false);
  const prevRef = useRef(prices);

  const refresh = useCallback(async () => {
    try {
      const binance = await fetchBinancePrices();
      setBinanceConnected(true);
      const synthetic = syntheticPrices(prevRef.current);
      const merged = { ...prevRef.current, ...synthetic, ...binance };
      prevRef.current = merged;
      setPrices(merged);
    } catch {
      setBinanceConnected(false);
      // Still update synthetic prices
      const synthetic = syntheticPrices(prevRef.current);
      const merged = { ...prevRef.current, ...synthetic };
      prevRef.current = merged;
      setPrices(merged);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, intervalMs);
    return () => clearInterval(id);
  }, [refresh, intervalMs]);

  return { prices, binanceConnected };
}
