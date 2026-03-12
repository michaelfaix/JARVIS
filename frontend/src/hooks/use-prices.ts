// =============================================================================
// src/hooks/use-prices.ts — Live prices via Binance WebSocket + REST fallback
//
// Crypto (BTC, ETH, SOL): Real-time via Binance WebSocket combined stream.
// Non-crypto: Synthetic random-walk prices updated on an interval.
// Falls back to REST polling if WebSocket fails.
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

const REVERSE_BINANCE: Record<string, string> = {};
for (const [symbol, binanceSymbol] of Object.entries(BINANCE_SYMBOLS)) {
  REVERSE_BINANCE[binanceSymbol.toLowerCase()] = symbol;
}

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
  for (const [symbol, binanceSymbol] of Object.entries(BINANCE_SYMBOLS)) {
    const ticker = data.find((d) => d.symbol === binanceSymbol);
    if (ticker) {
      prices[symbol] = parseFloat(ticker.price);
    }
  }
  return prices;
}

// Deterministic-ish walk for non-crypto
function syntheticPrices(
  prev: Record<string, number>
): Record<string, number> {
  const prices: Record<string, number> = {};
  for (const [symbol, base] of Object.entries(FALLBACK_BASE)) {
    const current = prev[symbol] ?? base;
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
  const [wsConnected, setWsConnected] = useState(false);
  const prevRef = useRef(prices);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
  const reconnectAttempts = useRef(0);

  // Update synthetic prices on interval
  useEffect(() => {
    const id = setInterval(() => {
      const synthetic = syntheticPrices(prevRef.current);
      prevRef.current = { ...prevRef.current, ...synthetic };
      setPrices((p) => ({ ...p, ...synthetic }));
    }, intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);

  // Binance WebSocket for real-time crypto prices
  const connectWs = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const streams = Object.values(BINANCE_SYMBOLS)
        .map((s) => `${s.toLowerCase()}@miniTicker`)
        .join("/");
      const ws = new WebSocket(
        `wss://stream.binance.com:9443/stream?streams=${streams}`
      );

      ws.onopen = () => {
        setWsConnected(true);
        setBinanceConnected(true);
        reconnectAttempts.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          // Combined stream format: { stream: "btcusdt@miniTicker", data: { s: "BTCUSDT", c: "65000.00" } }
          const data = msg.data;
          if (!data?.s) return;
          const symbol = REVERSE_BINANCE[data.s.toLowerCase()];
          if (!symbol) return;
          const price = parseFloat(data.c); // "c" = close price in miniTicker
          if (isNaN(price)) return;

          prevRef.current = { ...prevRef.current, [symbol]: price };
          setPrices((p) => ({ ...p, [symbol]: price }));
        } catch {
          // ignore parse errors
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
        wsRef.current = null;
        // Reconnect with backoff
        const delay = Math.min(1000 * 2 ** reconnectAttempts.current, 30000);
        reconnectAttempts.current++;
        if (reconnectAttempts.current <= 10) {
          reconnectTimer.current = setTimeout(connectWs, delay);
        }
      };

      ws.onerror = () => {
        ws.close();
      };

      wsRef.current = ws;
    } catch {
      // WebSocket not available, fall back to REST
      setWsConnected(false);
    }
  }, []);

  // REST fallback: fetch once on mount and as fallback
  const fetchRest = useCallback(async () => {
    try {
      const binance = await fetchBinancePrices();
      setBinanceConnected(true);
      prevRef.current = { ...prevRef.current, ...binance };
      setPrices((p) => ({ ...p, ...binance }));
    } catch {
      setBinanceConnected(false);
    }
  }, []);

  useEffect(() => {
    // Try WebSocket first, REST as initial data
    fetchRest();
    connectWs();

    // REST fallback polling if WS is down
    const restFallbackId = setInterval(() => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        fetchRest();
      }
    }, intervalMs);

    return () => {
      clearInterval(restFallbackId);
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connectWs, fetchRest, intervalMs]);

  return { prices, binanceConnected, wsConnected };
}
