// =============================================================================
// src/lib/constants.ts — App constants
// =============================================================================

export const DEFAULT_ASSETS = [
  { symbol: "BTC", name: "Bitcoin", price: 65000 },
  { symbol: "ETH", name: "Ethereum", price: 3200 },
  { symbol: "SOL", name: "Solana", price: 145 },
  { symbol: "SPY", name: "S&P 500 ETF", price: 520 },
  { symbol: "AAPL", name: "Apple", price: 195 },
  { symbol: "NVDA", name: "NVIDIA", price: 890 },
  { symbol: "TSLA", name: "Tesla", price: 175 },
  { symbol: "GLD", name: "Gold ETF", price: 215 },
] as const;

export const DEFAULT_CAPITAL = 100_000;

export const STRATEGIES = [
  { id: "momentum", label: "Momentum" },
  { id: "mean_reversion", label: "Mean Reversion" },
  { id: "combined", label: "Combined" },
  { id: "breakout", label: "Breakout" },
  { id: "trend_following", label: "Trend Following" },
] as const;

export type StrategyId = (typeof STRATEGIES)[number]["id"];

// Tier limits
export const TIER_LIMITS = {
  free: {
    maxAssets: 3,
    maxCapital: 10_000,
    signalDelayMinutes: 15,
    showOod: false,
    maxStrategies: 1,
  },
  pro: {
    maxAssets: Infinity,
    maxCapital: 500_000,
    signalDelayMinutes: 0,
    showOod: true,
    maxStrategies: 8,
  },
  enterprise: {
    maxAssets: Infinity,
    maxCapital: Infinity,
    signalDelayMinutes: 0,
    showOod: true,
    maxStrategies: Infinity,
  },
} as const;

export const FREE_ASSETS: string[] = DEFAULT_ASSETS.slice(0, 3).map((a) => a.symbol); // BTC, ETH, SOL
