// =============================================================================
// src/hooks/use-jarvis.ts — Custom hooks for JARVIS API data
// =============================================================================

"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getHealth,
  getMetrics,
  getSystemStatus,
  type MetricsResponse,
  type SystemStatusResponse,
} from "@/lib/api";

// ---------------------------------------------------------------------------
// useSystemStatus — polls /status every interval
// ---------------------------------------------------------------------------

interface UseSystemStatusResult {
  status: SystemStatusResponse | null;
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useSystemStatus(intervalMs = 5000): UseSystemStatusResult {
  const [status, setStatus] = useState<SystemStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await getSystemStatus();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connection failed");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, intervalMs);
    return () => clearInterval(id);
  }, [refresh, intervalMs]);

  return { status, loading, error, refresh };
}

// ---------------------------------------------------------------------------
// useMetrics — polls /metrics every interval
// ---------------------------------------------------------------------------

interface UseMetricsResult {
  metrics: MetricsResponse | null;
  loading: boolean;
  error: string | null;
}

export function useMetrics(intervalMs = 5000): UseMetricsResult {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function poll() {
      try {
        const data = await getMetrics();
        setMetrics(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Connection failed");
      } finally {
        setLoading(false);
      }
    }
    poll();
    const id = setInterval(poll, intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);

  return { metrics, loading, error };
}

// ---------------------------------------------------------------------------
// useBackendHealth — checks /health once
// ---------------------------------------------------------------------------

export function useBackendHealth(): {
  connected: boolean;
  checking: boolean;
} {
  const [connected, setConnected] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    getHealth()
      .then(() => setConnected(true))
      .catch(() => setConnected(false))
      .finally(() => setChecking(false));
  }, []);

  return { connected, checking };
}
