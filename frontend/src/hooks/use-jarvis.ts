// =============================================================================
// src/hooks/use-jarvis.ts — Custom hooks for JARVIS API data
// =============================================================================

"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getHealth,
  getMetrics,
  getSystemStatus,
  getLastApiLatency,
  type MetricsResponse,
  type SystemStatusResponse,
} from "@/lib/api";
import { inferRegime, type RegimeState } from "@/lib/types";

// ---------------------------------------------------------------------------
// useSystemStatus — polls /status every interval
// ---------------------------------------------------------------------------

interface UseSystemStatusResult {
  status: SystemStatusResponse | null;
  regime: RegimeState;
  loading: boolean;
  error: string | null;
  lastUpdated: number | null;
  apiLatencyMs: number | null;
  refresh: () => void;
}

export function useSystemStatus(intervalMs = 5000): UseSystemStatusResult {
  const [status, setStatus] = useState<SystemStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);
  const [apiLatencyMs, setApiLatencyMs] = useState<number | null>(null);

  const regime = useMemo<RegimeState>(
    () => (status ? inferRegime(status.modus) : "RISK_ON"),
    [status]
  );

  const refresh = useCallback(async () => {
    try {
      const data = await getSystemStatus();
      setStatus(data);
      setError(null);
      setLastUpdated(Date.now());
      setApiLatencyMs(getLastApiLatency());
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

  return { status, regime, loading, error, lastUpdated, apiLatencyMs, refresh };
}

// ---------------------------------------------------------------------------
// useMetrics — polls /metrics every interval
// ---------------------------------------------------------------------------

interface UseMetricsResult {
  metrics: MetricsResponse | null;
  loading: boolean;
  error: string | null;
  lastUpdated: number | null;
  refresh: () => void;
}

export function useMetrics(intervalMs = 5000): UseMetricsResult {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await getMetrics();
      setMetrics(data);
      setError(null);
      setLastUpdated(Date.now());
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

  return { metrics, loading, error, lastUpdated, refresh };
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
