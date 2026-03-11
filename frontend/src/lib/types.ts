// =============================================================================
// src/lib/types.ts — Shared frontend types
// =============================================================================

// ---------------------------------------------------------------------------
// Regime & System
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// Signals
// ---------------------------------------------------------------------------

export interface Signal {
  id: string;
  asset: string;
  direction: "LONG" | "SHORT";
  entry: number;
  stopLoss: number;
  takeProfit: number;
  confidence: number;
  qualityScore: number;
  regime: string;
  isOod: boolean;
  timestamp: Date;
}

// ---------------------------------------------------------------------------
// Portfolio (Paper Trading)
// ---------------------------------------------------------------------------

export interface Position {
  id: string;
  asset: string;
  direction: "LONG" | "SHORT";
  entryPrice: number;
  currentPrice: number;
  size: number;
  capitalAllocated: number;
  openedAt: string; // ISO string for serialization
  pnl: number;
  pnlPercent: number;
}

export interface PortfolioState {
  totalCapital: number;
  availableCapital: number;
  positions: Position[];
  realizedPnl: number;
}

// ---------------------------------------------------------------------------
// Opportunity Radar
// ---------------------------------------------------------------------------

export interface Opportunity {
  asset: string;
  direction: "LONG" | "SHORT";
  score: number;
  confidence: number;
  momentum: number;
  regime: RegimeState;
  qualityScore: number;
  price: number;
}

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

export interface AppSettings {
  paperCapital: number;
  strategy: "momentum" | "mean_reversion" | "combined";
  theme: "dark" | "light";
  pollIntervalMs: number;
  trackedAssets: string[];
}

// ---------------------------------------------------------------------------
// Chart
// ---------------------------------------------------------------------------

export interface CandlestickData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

export function inferRegime(modus: string): RegimeState {
  switch (modus) {
    case "NORMAL":
      return "RISK_ON";
    case "ERHOEHTE_VORSICHT":
    case "REDUZIERTES_VERTRAUEN":
      return "RISK_OFF";
    case "NOTFALL_MODUS":
    case "KONFIDENZ_KOLLAPS":
      return "CRISIS";
    case "MINIMALE_EXPOSITION":
    case "NUR_MONITORING":
      return "TRANSITION";
    default:
      return "RISK_ON";
  }
}
