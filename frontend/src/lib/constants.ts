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
] as const;

export type StrategyId = (typeof STRATEGIES)[number]["id"];
