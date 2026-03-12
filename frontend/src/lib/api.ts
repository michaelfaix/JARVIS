// =============================================================================
// src/lib/api.ts — JARVIS Backend API Client
// =============================================================================

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const WS_BASE =
  process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1/stream";

// ---------------------------------------------------------------------------
// Types matching jarvis/api/models.py
// ---------------------------------------------------------------------------

export interface HealthResponse {
  status: string;
}

export interface UncertaintyOutput {
  aleatoric: number;
  epistemic_model: number;
  epistemic_data: number;
  total: number;
}

export interface PredictionRequest {
  features: Record<string, number>;
  regime: string;
  force_deep_path?: boolean;
}

export interface PredictionResponse {
  mu: number;
  sigma: number;
  confidence: number;
  deep_path_used: boolean;
  uncertainty: UncertaintyOutput;
  quality_score: number;
  regime: string;
  is_ood: boolean;
  ood_score: number;
}

export interface SystemStatusResponse {
  modus: string;
  vorhersagen_aktiv: boolean;
  konfidenz_multiplikator: number;
  ece: number;
  ood_score: number;
  meta_unsicherheit: number;
  entscheidungs_count: number;
}

export interface MetricsResponse {
  quality_score: number;
  calibration_component: number;
  confidence_component: number;
  stability_component: number;
  data_quality_component: number;
  regime_component: number;
}

// ---------------------------------------------------------------------------
// API Latency tracking
// ---------------------------------------------------------------------------

let _lastLatencyMs: number | null = null;

/** Returns the latency of the most recent API call in milliseconds. */
export function getLastApiLatency(): number | null {
  return _lastLatencyMs;
}

// ---------------------------------------------------------------------------
// Core fetch
// ---------------------------------------------------------------------------

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const start = performance.now();
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  _lastLatencyMs = Math.round(performance.now() - start);
  if (!res.ok) {
    throw new Error(`API Error ${res.status}: ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Endpoints
// ---------------------------------------------------------------------------

export async function getHealth(): Promise<HealthResponse> {
  return fetchApi<HealthResponse>("/health");
}

export async function getSystemStatus(): Promise<SystemStatusResponse> {
  return fetchApi<SystemStatusResponse>("/status");
}

export async function getMetrics(): Promise<MetricsResponse> {
  return fetchApi<MetricsResponse>("/metrics");
}

export async function postPrediction(
  req: PredictionRequest
): Promise<PredictionResponse> {
  return fetchApi<PredictionResponse>("/predict", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

// ---------------------------------------------------------------------------
// Batch predictions for multiple assets
// ---------------------------------------------------------------------------

export interface AssetPrediction {
  asset: string;
  prediction: PredictionResponse | null;
  error: string | null;
}

export async function batchPredict(
  assets: { symbol: string; features: Record<string, number> }[],
  regime: string
): Promise<AssetPrediction[]> {
  const results = await Promise.allSettled(
    assets.map((a) =>
      postPrediction({ features: a.features, regime }).then((pred) => ({
        asset: a.symbol,
        prediction: pred,
        error: null as string | null,
      }))
    )
  );

  return results.map((r, i) => {
    if (r.status === "fulfilled") return r.value;
    return {
      asset: assets[i].symbol,
      prediction: null,
      error: r.reason instanceof Error ? r.reason.message : "Unknown error",
    };
  });
}
