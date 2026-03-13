// =============================================================================
// src/hooks/use-websocket.ts — WebSocket connection to JARVIS backend
//
// Connects to /api/v1/stream/{symbol} for real-time data streaming.
// Auto-reconnects on disconnect with exponential backoff.
// =============================================================================

"use client";

import { useCallback, useEffect, useRef, useState } from "react";

const WS_BASE =
  process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1/stream";

export type WsStatus = "connecting" | "connected" | "disconnected";

interface UseWebSocketOptions {
  /** Auto-reconnect on disconnect (default true) */
  reconnect?: boolean;
  /** Max reconnect attempts (default 10) */
  maxRetries?: number;
  /** Initial reconnect delay in ms (default 1000) */
  baseDelay?: number;
}

interface WsMessage {
  type: string;
  symbol: string;
  data?: Record<string, unknown>;
  timestamp?: string;
}

export function useWebSocket(
  symbol: string | null,
  onMessage?: (msg: WsMessage) => void,
  options: UseWebSocketOptions = {}
) {
  const { reconnect = true, maxRetries = 10, baseDelay = 1000 } = options;

  const [status, setStatus] = useState<WsStatus>("disconnected");
  const [lastMessage, setLastMessage] = useState<WsMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  const cleanup = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.onopen = null;
      wsRef.current.onclose = null;
      wsRef.current.onmessage = null;
      wsRef.current.onerror = null;
      if (
        wsRef.current.readyState === WebSocket.OPEN ||
        wsRef.current.readyState === WebSocket.CONNECTING
      ) {
        wsRef.current.close();
      }
      wsRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (!symbol || !mountedRef.current) return;

    cleanup();
    setStatus("connecting");

    try {
      const ws = new WebSocket(`${WS_BASE}/${symbol}`);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current) return;
        retriesRef.current = 0;
        setStatus("connected");
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;
        try {
          const msg: WsMessage = JSON.parse(event.data);
          setLastMessage(msg);
          onMessageRef.current?.(msg);
        } catch {
          // Non-JSON message, ignore
        }
      };

      ws.onclose = () => {
        if (!mountedRef.current) return;
        setStatus("disconnected");
        wsRef.current = null;

        if (reconnect && retriesRef.current < maxRetries) {
          const delay = Math.min(
            baseDelay * Math.pow(2, retriesRef.current),
            30000
          );
          retriesRef.current += 1;
          timerRef.current = setTimeout(() => {
            if (mountedRef.current) connect();
          }, delay);
        }
      };

      ws.onerror = () => {
        // onclose will fire after onerror
      };
    } catch {
      setStatus("disconnected");
    }
  }, [symbol, cleanup, reconnect, maxRetries, baseDelay]);

  const send = useCallback(
    (data: Record<string, unknown>) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify(data));
      }
    },
    []
  );

  const disconnect = useCallback(() => {
    retriesRef.current = maxRetries; // Prevent reconnect
    cleanup();
    setStatus("disconnected");
  }, [cleanup, maxRetries]);

  // Connect on mount / symbol change
  useEffect(() => {
    mountedRef.current = true;
    if (symbol) {
      connect();
    }
    return () => {
      mountedRef.current = false;
      cleanup();
    };
  }, [symbol, connect, cleanup]);

  // Heartbeat ping every 30s to keep connection alive
  useEffect(() => {
    if (status !== "connected") return;
    const id = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "ping" }));
      }
    }, 30000);
    return () => clearInterval(id);
  }, [status]);

  // Reconnect when tab becomes visible
  useEffect(() => {
    if (!symbol) return;
    const handleVisibility = () => {
      if (document.visibilityState === "visible" && status === "disconnected" && mountedRef.current) {
        retriesRef.current = 0;
        connect();
      }
    };
    document.addEventListener("visibilitychange", handleVisibility);
    return () => document.removeEventListener("visibilitychange", handleVisibility);
  }, [symbol, status, connect]);

  return { status, lastMessage, send, disconnect };
}
