// =============================================================================
// src/lib/types.ts — Shared frontend types
// =============================================================================

export type RegimeState =
  | "RISK_ON"
  | "RISK_OFF"
  | "CRISIS"
  | "TRANSITION"
  | "UNKNOWN";

export type SystemModus =
  | "NORMAL"
  | "ERHOEHTE_VORSICHT"
  | "REDUZIERTES_VERTRAUEN"
  | "MINIMALE_EXPOSITION"
  | "NUR_MONITORING"
  | "NOTFALL_MODUS"
  | "DATEN_QUARANTAENE"
  | "MODELL_ROLLBACK"
  | "KONFIDENZ_KOLLAPS";

export interface CandlestickData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface SignalOverlay {
  time: string;
  value: number;
  color: string;
}

export const REGIME_COLORS: Record<RegimeState, string> = {
  RISK_ON: "#22c55e",
  RISK_OFF: "#eab308",
  CRISIS: "#ef4444",
  TRANSITION: "#3b82f6",
  UNKNOWN: "#6b7280",
};

export const REGIME_LABELS: Record<RegimeState, string> = {
  RISK_ON: "Risk On",
  RISK_OFF: "Risk Off",
  CRISIS: "Crisis",
  TRANSITION: "Transition",
  UNKNOWN: "Unknown",
};

export const MODUS_COLORS: Record<string, string> = {
  NORMAL: "#22c55e",
  ERHOEHTE_VORSICHT: "#84cc16",
  REDUZIERTES_VERTRAUEN: "#eab308",
  MINIMALE_EXPOSITION: "#f97316",
  NUR_MONITORING: "#f97316",
  NOTFALL_MODUS: "#ef4444",
  DATEN_QUARANTAENE: "#ef4444",
  MODELL_ROLLBACK: "#dc2626",
  KONFIDENZ_KOLLAPS: "#991b1b",
};
