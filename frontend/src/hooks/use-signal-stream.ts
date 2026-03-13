// =============================================================================
// src/hooks/use-signal-stream.ts — WebSocket stream for live signals
//
// Connects to the JARVIS backend WebSocket at /stream/{symbol}.
// Receives real-time signal updates, reducing polling latency.
// Gracefully falls back to polling if WS is unavailable.
// =============================================================================

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { WS_BASE } from "@/lib/api";
import type { Signal } from "@/lib/types";

interface StreamMessage {
  type: "signal" | "status" | "heartbeat";
  data?: {
    symbol: string;
    mu: number;
    sigma: number;
    confidence: number;
    quality_score: number;
    regime: string;
    is_ood: boolean;
    ood_score: number;
    uncertainty?: {
      aleatoric: number;
      epistemic_model: number;
      epistemic_data: number;
      total: number;
    };
    deep_path_used: boolean;
  };
}

export function useSignalStream(
  symbols: string[],
  prices: Record<string, number>
) {
  const [streamSignals, setStreamSignals] = useState<
    Map<string, Signal>
  >(new Map());
  const [connected, setConnected] = useState(false);
  const wsRefs = useRef<Map<string, WebSocket>>(new Map());
  const mountedRef = useRef(true);
  const pricesRef = useRef(prices);
  pricesRef.current = prices;

  const connectSymbol = useCallback((symbol: string) => {
    if (!mountedRef.current) return;
    if (wsRefs.current.has(symbol)) return;

    try {
      const ws = new WebSocket(`${WS_BASE}/${symbol}`);

      ws.onopen = () => {
        if (!mountedRef.current) {
          ws.close();
          return;
        }
        ws.send("subscribe");
        setConnected(true);
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;
        try {
          const msg: StreamMessage = JSON.parse(event.data);
          if (msg.type !== "signal" || !msg.data) return;

          const d = msg.data;
          const livePrice = pricesRef.current[d.symbol] ?? 0;
          if (livePrice <= 0) return;

          const direction: "LONG" | "SHORT" = d.mu >= 0 ? "LONG" : "SHORT";
          const sigma = Math.max(d.sigma, 0.001);

          const signal: Signal = {
            id: `ws-${d.symbol}-${Date.now()}`,
            asset: d.symbol,
            direction,
            entry: livePrice,
            stopLoss:
              direction === "LONG"
                ? livePrice * (1 - sigma * 2)
                : livePrice * (1 + sigma * 2),
            takeProfit:
              direction === "LONG"
                ? livePrice * (1 + sigma * 3)
                : livePrice * (1 - sigma * 3),
            confidence: d.confidence,
            qualityScore: d.quality_score,
            regime: d.regime,
            isOod: d.is_ood,
            oodScore: d.ood_score,
            uncertainty: d.uncertainty ?? null,
            deepPathUsed: d.deep_path_used,
            timestamp: new Date(),
          };

          setStreamSignals((prev) => {
            const next = new Map(prev);
            next.set(d.symbol, signal);
            return next;
          });
        } catch {
          // ignore parse errors
        }
      };

      ws.onclose = () => {
        wsRefs.current.delete(symbol);
        if (mountedRef.current && wsRefs.current.size === 0) {
          setConnected(false);
        }
      };

      ws.onerror = () => {
        ws.close();
      };

      wsRefs.current.set(symbol, ws);
    } catch {
      // WS not available
    }
  }, []);

  const closeAll = useCallback(() => {
    wsRefs.current.forEach((ws) => {
      ws.onclose = null;
      ws.onerror = null;
      ws.onmessage = null;
      ws.close();
    });
    wsRefs.current.clear();
    setConnected(false);
  }, []);

  // Connect to all symbols on mount
  useEffect(() => {
    mountedRef.current = true;
    for (const symbol of symbols) {
      connectSymbol(symbol);
    }
    return () => {
      mountedRef.current = false;
      closeAll();
    };
  }, [symbols, connectSymbol, closeAll]);

  return {
    streamSignals: Array.from(streamSignals.values()),
    wsConnected: connected,
  };
}
