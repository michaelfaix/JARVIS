// =============================================================================
// src/hooks/use-prices.ts — Live prices via Binance WebSocket + REST fallback
//
// Crypto (BTC, ETH, SOL): Real-time via Binance WebSocket combined stream.
// Non-crypto: Synthetic random-walk prices updated every 1 second.
// Falls back to REST polling if WebSocket fails.
// Visibility API: reconnects when tab becomes visible again.
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

// Random-walk for non-crypto: ±0.01–0.05% per tick, with mean reversion
function syntheticPrices(
  prev: Record<string, number>
): Record<string, number> {
  const prices: Record<string, number> = {};
  for (const [symbol, base] of Object.entries(FALLBACK_BASE)) {
    const current = prev[symbol] ?? base;
    const pctMove =
      (Math.random() * 0.0004 + 0.0001) * (Math.random() > 0.5 ? 1 : -1);
    const reversion = ((base - current) / base) * 0.0002;
    prices[symbol] = parseFloat(
      (current * (1 + pctMove + reversion)).toFixed(2)
    );
  }
  return prices;
}

const HISTORY_SIZE = 20; // ring buffer size for sparklines

export function usePrices(intervalMs: number = 5000) {
  const [prices, setPrices] = useState<Record<string, number>>(() => {
    const initial: Record<string, number> = {};
    for (const a of DEFAULT_ASSETS) {
      initial[a.symbol] = a.price;
    }
    return initial;
  });
  const [priceHistory, setPriceHistory] = useState<Record<string, number[]>>({});
  const [binanceConnected, setBinanceConnected] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const prevRef = useRef(prices);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
  const mountedRef = useRef(true);

  // --- Synthetic prices every 1s ---
  useEffect(() => {
    const id = setInterval(() => {
      const synthetic = syntheticPrices(prevRef.current);
      prevRef.current = { ...prevRef.current, ...synthetic };
      setPrices((p) => ({ ...p, ...synthetic }));
    }, 1000);
    return () => clearInterval(id);
  }, []);

  // --- Price history ring buffer: snapshot every 3s ---
  useEffect(() => {
    const id = setInterval(() => {
      setPriceHistory((prev) => {
        const next = { ...prev };
        for (const [symbol, price] of Object.entries(prevRef.current)) {
          const arr = next[symbol] ? [...next[symbol]] : [];
          arr.push(price);
          if (arr.length > HISTORY_SIZE) arr.shift();
          next[symbol] = arr;
        }
        return next;
      });
    }, 3000);
    return () => clearInterval(id);
  }, []);

  // --- WebSocket connection ---
  const closeWs = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = undefined;
    }
    if (wsRef.current) {
      // Remove onclose to prevent reconnect during cleanup
      wsRef.current.onclose = null;
      wsRef.current.onerror = null;
      wsRef.current.onmessage = null;
      wsRef.current.close();
      wsRef.current = null;
    }
    setWsConnected(false);
  }, []);

  const connectWs = useCallback(() => {
    if (!mountedRef.current) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    // Clean up any existing connection first
    closeWs();

    try {
      const streams = Object.values(BINANCE_SYMBOLS)
        .map((s) => `${s.toLowerCase()}@miniTicker`)
        .join("/");
      const ws = new WebSocket(
        `wss://stream.binance.com:9443/stream?streams=${streams}`
      );

      ws.onopen = () => {
        if (!mountedRef.current) {
          ws.close();
          return;
        }
        setWsConnected(true);
        setBinanceConnected(true);
        reconnectTimer.current = undefined;
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;
        try {
          const msg = JSON.parse(event.data);
          const data = msg.data;
          if (!data?.s) return;
          const symbol = REVERSE_BINANCE[data.s.toLowerCase()];
          if (!symbol) return;
          const price = parseFloat(data.c);
          if (isNaN(price)) return;

          prevRef.current = { ...prevRef.current, [symbol]: price };
          setPrices((p) => ({ ...p, [symbol]: price }));
        } catch {
          // ignore parse errors
        }
      };

      ws.onclose = () => {
        if (!mountedRef.current) return;
        setWsConnected(false);
        wsRef.current = null;
        // Reconnect with backoff
        const attempts = reconnectTimer.current ? 1 : 0;
        const delay = Math.min(1000 * 2 ** attempts, 30000);
        reconnectTimer.current = setTimeout(() => {
          if (mountedRef.current) connectWs();
        }, delay);
      };

      ws.onerror = () => {
        ws.close();
      };

      wsRef.current = ws;
    } catch {
      setWsConnected(false);
    }
  }, [closeWs]);

  // --- REST fallback ---
  const fetchRest = useCallback(async () => {
    if (!mountedRef.current) return;
    try {
      const binance = await fetchBinancePrices();
      if (!mountedRef.current) return;
      setBinanceConnected(true);
      prevRef.current = { ...prevRef.current, ...binance };
      setPrices((p) => ({ ...p, ...binance }));
    } catch {
      if (mountedRef.current) setBinanceConnected(false);
    }
  }, []);

  // --- Main effect: connect on mount, clean on unmount ---
  useEffect(() => {
    mountedRef.current = true;

    fetchRest();
    connectWs();

    // REST fallback polling if WS is down
    const restFallbackId = setInterval(() => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        fetchRest();
      }
    }, intervalMs);

    return () => {
      mountedRef.current = false;
      clearInterval(restFallbackId);
      closeWs();
    };
  }, [connectWs, fetchRest, closeWs, intervalMs]);

  // --- Visibility API: reconnect when tab becomes visible ---
  useEffect(() => {
    const handleVisibility = () => {
      if (document.visibilityState === "visible" && mountedRef.current) {
        // Reconnect WS if not connected
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
          connectWs();
        }
        // Refresh REST prices immediately
        fetchRest();
      }
    };
    document.addEventListener("visibilitychange", handleVisibility);
    return () =>
      document.removeEventListener("visibilitychange", handleVisibility);
  }, [connectWs, fetchRest]);

  return { prices, priceHistory, binanceConnected, wsConnected };
}
