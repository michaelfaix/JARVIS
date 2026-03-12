// =============================================================================
// src/hooks/use-binance-klines.ts — Fetch real OHLC klines from Binance
// =============================================================================

"use client";

import { useCallback, useEffect, useState } from "react";

const BINANCE_SYMBOLS: Record<string, string> = {
  BTC: "BTCUSDT",
  ETH: "ETHUSDT",
  SOL: "SOLUSDT",
};

export interface Kline {
  time: number; // Unix timestamp in seconds (UTCTimestamp for lightweight-charts)
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// Binance interval strings
const INTERVAL_MAP: Record<string, string> = {
  "1m": "1m",
  "5m": "5m",
  "15m": "15m",
  "1h": "1h",
  "4h": "4h",
  "1d": "1d",
  "1w": "1w",
};

// Sensible candle counts per timeframe
const LIMIT_MAP: Record<string, number> = {
  "1m": 60,   // last hour
  "5m": 72,   // last 6 hours
  "15m": 96,  // last 24 hours
  "1h": 90,   // last ~4 days
  "4h": 90,   // last ~15 days
  "1d": 90,   // last 90 days
  "1w": 52,   // last year
};

export function useBinanceKlines(
  symbol: string,
  interval: string = "1d",
  limit?: number
) {
  const [klines, setKlines] = useState<Kline[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isCrypto = symbol in BINANCE_SYMBOLS;
  const binanceInterval = INTERVAL_MAP[interval] ?? "1d";
  const effectiveLimit = limit ?? LIMIT_MAP[interval] ?? 90;

  const fetch_ = useCallback(async () => {
    if (!isCrypto) {
      setKlines([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const binanceSymbol = BINANCE_SYMBOLS[symbol];
      const url = `https://api.binance.com/api/v3/klines?symbol=${binanceSymbol}&interval=${binanceInterval}&limit=${effectiveLimit}`;
      const res = await globalThis.fetch(url);
      if (!res.ok) throw new Error(`Binance ${res.status}`);

      const data: unknown[][] = await res.json();

      const parsed: Kline[] = data.map((k) => {
        const openTime = k[0] as number;
        // Unix timestamp in seconds (lightweight-charts UTCTimestamp)
        const time = Math.floor(openTime / 1000);

        return {
          time,
          open: parseFloat(k[1] as string),
          high: parseFloat(k[2] as string),
          low: parseFloat(k[3] as string),
          close: parseFloat(k[4] as string),
          volume: parseFloat(k[5] as string),
        };
      });

      setKlines(parsed);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch klines");
      setKlines([]);
    } finally {
      setLoading(false);
    }
  }, [symbol, binanceInterval, effectiveLimit, isCrypto]);

  useEffect(() => {
    fetch_();
  }, [fetch_]);

  return { klines, loading, error, isCrypto, refetch: fetch_ };
}
