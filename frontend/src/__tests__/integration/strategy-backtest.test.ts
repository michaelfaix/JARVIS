import { runBacktest, type BacktestConfig } from "@/lib/backtest-engine";

describe("Backtest Engine", () => {
  const baseConfig: BacktestConfig = {
    strategy: "combined",
    assets: ["BTC", "ETH"],
    period: 90,
    initialCapital: 100000,
    riskPerTrade: 2,
    slPercent: 3,
    tpPercent: 6,
  };

  it("runs without errors", () => {
    expect(() => runBacktest(baseConfig)).not.toThrow();
  });

  it("returns correct result structure", () => {
    const result = runBacktest(baseConfig);
    expect(result).toHaveProperty("totalReturn");
    expect(result).toHaveProperty("winRate");
    expect(result).toHaveProperty("totalTrades");
    expect(result).toHaveProperty("profitFactor");
    expect(result).toHaveProperty("maxDrawdown");
    expect(result).toHaveProperty("sharpeRatio");
    expect(result).toHaveProperty("avgWin");
    expect(result).toHaveProperty("avgLoss");
    expect(result).toHaveProperty("equityCurve");
    expect(result).toHaveProperty("trades");
  });

  it("starts with initial capital in equity curve", () => {
    const result = runBacktest(baseConfig);
    expect(result.equityCurve.length).toBeGreaterThan(0);
    expect(result.equityCurve[0].equity).toBe(baseConfig.initialCapital);
  });

  it("win rate is between 0 and 100", () => {
    const result = runBacktest(baseConfig);
    expect(result.winRate).toBeGreaterThanOrEqual(0);
    expect(result.winRate).toBeLessThanOrEqual(100);
  });

  it("max drawdown is non-negative", () => {
    const result = runBacktest(baseConfig);
    expect(result.maxDrawdown).toBeGreaterThanOrEqual(0);
  });

  it("profit factor is non-negative", () => {
    const result = runBacktest(baseConfig);
    expect(result.profitFactor).toBeGreaterThanOrEqual(0);
  });

  it("runs momentum strategy", () => {
    const result = runBacktest({ ...baseConfig, strategy: "momentum" });
    expect(result.totalTrades).toBeGreaterThan(0);
  });

  it("runs mean_reversion strategy", () => {
    const result = runBacktest({ ...baseConfig, strategy: "mean_reversion" });
    expect(result.totalTrades).toBeGreaterThan(0);
  });

  it("runs scalping strategy", () => {
    const result = runBacktest({ ...baseConfig, strategy: "scalping" });
    expect(result.totalTrades).toBeGreaterThan(0);
  });

  it("handles single asset", () => {
    const result = runBacktest({ ...baseConfig, assets: ["BTC"] });
    expect(result.totalTrades).toBeGreaterThan(0);
  });

  it("equity curve has at least 2 data points", () => {
    const result = runBacktest({ ...baseConfig, period: 30 });
    expect(result.equityCurve.length).toBeGreaterThanOrEqual(2);
  });

  it("trades have valid structure", () => {
    const result = runBacktest(baseConfig);
    if (result.trades.length > 0) {
      const trade = result.trades[0];
      expect(trade).toHaveProperty("asset");
      expect(trade).toHaveProperty("direction");
      expect(trade).toHaveProperty("entry");
      expect(trade).toHaveProperty("exit");
      expect(trade).toHaveProperty("pnl");
      expect(["LONG", "SHORT"]).toContain(trade.direction);
      expect(["TP", "SL", "SIGNAL"]).toContain(trade.exitReason);
    }
  });
});
