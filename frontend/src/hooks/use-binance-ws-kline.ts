// =============================================================================
// src/hooks/use-binance-ws-kline.ts — Binance kline WebSocket for live candle
//
// Subscribes to wss://stream.binance.com/ws/<symbol>@kline_<interval>
// Returns the latest tick (price + OHLCV of the current forming candle).
// Only active for crypto assets (BTC, ETH, SOL).
// Visibility API: reconnects when tab becomes visible again.
// =============================================================================

"use client";

import { useCallback, useEffect, useRef, useState } from "react";

const BINANCE_SYMBOLS: Record<string, string> = {
  BTC: "btcusdt",
  ETH: "ethusdt",
  SOL: "solusdt",
};

export interface LiveKlineTick {
  time: number; // candle open time (unix seconds)
  open: number;
  high: number;
  low: number;
  close: number; // current price
  volume: number;
  isClosed: boolean; // true when the candle has finalized
}

export function useBinanceWsKline(symbol: string, interval: string = "1d") {
  const [tick, setTick] = useState<LiveKlineTick | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
  const attemptsRef = useRef(0);
  const mountedRef = useRef(true);

  const isCrypto = symbol in BINANCE_SYMBOLS;
  const binanceSymbol = BINANCE_SYMBOLS[symbol];

  const closeWs = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = undefined;
    }
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.onerror = null;
      wsRef.current.onmessage = null;
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnected(false);
  }, []);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;
    if (!isCrypto || !binanceSymbol) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    closeWs();

    try {
      const ws = new WebSocket(
        `wss://stream.binance.com:9443/ws/${binanceSymbol}@kline_${interval}`
      );

      ws.onopen = () => {
        if (!mountedRef.current) {
          ws.close();
          return;
        }
        attemptsRef.current = 0;
        setConnected(true);
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;
        try {
          const msg = JSON.parse(event.data);
          const k = msg.k;
          if (!k) return;

          setTick({
            time: Math.floor(k.t / 1000),
            open: parseFloat(k.o),
            high: parseFloat(k.h),
            low: parseFloat(k.l),
            close: parseFloat(k.c),
            volume: parseFloat(k.v),
            isClosed: k.x,
          });
        } catch {
          // ignore parse errors
        }
      };

      ws.onclose = () => {
        if (!mountedRef.current) return;
        setConnected(false);
        wsRef.current = null;
        // Reconnect with exponential backoff
        attemptsRef.current += 1;
        const delay = Math.min(1000 * 2 ** attemptsRef.current, 30000);
        reconnectTimer.current = setTimeout(() => {
          if (mountedRef.current) connect();
        }, delay);
      };

      ws.onerror = () => {
        ws.close();
      };

      wsRef.current = ws;
    } catch {
      setConnected(false);
    }
  }, [isCrypto, binanceSymbol, interval, closeWs]);

  // Main effect: connect on mount, clean on unmount
  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      closeWs();
      setTick(null);
    };
  }, [connect, closeWs]);

  // Visibility API: reconnect when tab becomes visible
  useEffect(() => {
    if (!isCrypto) return;
    const handleVisibility = () => {
      if (document.visibilityState === "visible" && mountedRef.current) {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
          connect();
        }
      }
    };
    document.addEventListener("visibilitychange", handleVisibility);
    return () =>
      document.removeEventListener("visibilitychange", handleVisibility);
  }, [connect, isCrypto]);

  return { tick, connected, isCrypto };
}
