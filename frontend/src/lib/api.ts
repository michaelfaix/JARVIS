// =============================================================================
// src/lib/api.ts — JARVIS Backend API Client
//
// Connects to FastAPI backend at localhost:8000/api/v1
// =============================================================================

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

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
  features: number[];
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
// API Functions
// ---------------------------------------------------------------------------

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API Error ${res.status}: ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

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
