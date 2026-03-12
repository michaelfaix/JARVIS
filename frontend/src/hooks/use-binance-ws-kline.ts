// =============================================================================
// src/hooks/use-binance-ws-kline.ts — Binance kline WebSocket for live candle
//
// Subscribes to wss://stream.binance.com/ws/<symbol>@kline_<interval>
// Returns the latest tick (price + OHLCV of the current forming candle).
// Only active for crypto assets (BTC, ETH, SOL).
// =============================================================================

"use client";

import { useCallback, useEffect, useRef, useState } from "react";

const BINANCE_SYMBOLS: Record<string, string> = {
  BTC: "btcusdt",
  ETH: "ethusdt",
  SOL: "solusdt",
};

export interface LiveKlineTick {
  time: number;      // candle open time (unix seconds)
  open: number;
  high: number;
  low: number;
  close: number;     // current price
  volume: number;
  isClosed: boolean; // true when the candle has finalized
}

export function useBinanceWsKline(symbol: string, interval: string = "1d") {
  const [tick, setTick] = useState<LiveKlineTick | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
  const reconnectAttempts = useRef(0);

  const isCrypto = symbol in BINANCE_SYMBOLS;
  const binanceSymbol = BINANCE_SYMBOLS[symbol];

  const connect = useCallback(() => {
    if (!isCrypto || !binanceSymbol) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(
        `wss://stream.binance.com:9443/ws/${binanceSymbol}@kline_${interval}`
      );

      ws.onopen = () => {
        setConnected(true);
        reconnectAttempts.current = 0;
      };

      ws.onmessage = (event) => {
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
        setConnected(false);
        wsRef.current = null;
        const delay = Math.min(1000 * 2 ** reconnectAttempts.current, 30000);
        reconnectAttempts.current++;
        if (reconnectAttempts.current <= 10) {
          reconnectTimer.current = setTimeout(connect, delay);
        }
      };

      ws.onerror = () => {
        ws.close();
      };

      wsRef.current = ws;
    } catch {
      setConnected(false);
    }
  }, [isCrypto, binanceSymbol, interval]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      setTick(null);
      setConnected(false);
      reconnectAttempts.current = 0;
    };
  }, [connect]);

  return { tick, connected, isCrypto };
}
