/**
 * Tests for sentiment calculation helpers (momentum, volatility, classify).
 */

describe("Sentiment helpers", () => {
  // --- classify ---
  function classify(value: number): string {
    if (value <= 25) return "Extreme Fear";
    if (value <= 45) return "Fear";
    if (value <= 55) return "Neutral";
    if (value <= 75) return "Greed";
    return "Extreme Greed";
  }

  it.each([
    [0, "Extreme Fear"],
    [10, "Extreme Fear"],
    [25, "Extreme Fear"],
    [26, "Fear"],
    [45, "Fear"],
    [50, "Neutral"],
    [55, "Neutral"],
    [60, "Greed"],
    [75, "Greed"],
    [80, "Extreme Greed"],
    [100, "Extreme Greed"],
  ])("classify(%i) = %s", (value, expected) => {
    expect(classify(value)).toBe(expected);
  });

  // --- momentumLabel ---
  function momentumLabel(score: number): string {
    if (score <= -50) return "Strong Bearish";
    if (score <= -15) return "Bearish";
    if (score <= 15) return "Neutral";
    if (score <= 50) return "Bullish";
    return "Strong Bullish";
  }

  it.each([
    [-100, "Strong Bearish"],
    [-50, "Strong Bearish"],
    [-30, "Bearish"],
    [0, "Neutral"],
    [15, "Neutral"],
    [30, "Bullish"],
    [80, "Strong Bullish"],
  ])("momentumLabel(%i) = %s", (score, expected) => {
    expect(momentumLabel(score)).toBe(expected);
  });

  // --- volatilityLabel ---
  function volatilityLabel(score: number): string {
    if (score < 33) return "Low";
    if (score < 66) return "Medium";
    return "High";
  }

  it.each([
    [0, "Low"],
    [32, "Low"],
    [33, "Medium"],
    [65, "Medium"],
    [66, "High"],
    [100, "High"],
  ])("volatilityLabel(%i) = %s", (score, expected) => {
    expect(volatilityLabel(score)).toBe(expected);
  });
});

describe("Momentum from price history", () => {
  function calculateMomentumFromHistory(
    priceHistory: Record<string, number[]>
  ): number {
    const symbols = ["BTC", "ETH", "SOL"];
    let totalPct = 0;
    let count = 0;
    for (const sym of symbols) {
      const hist = priceHistory[sym];
      if (!hist || hist.length < 2) continue;
      const first = hist[0];
      const last = hist[hist.length - 1];
      if (first > 0) {
        totalPct += ((last - first) / first) * 100;
        count++;
      }
    }
    if (count === 0) return 0;
    const avg = totalPct / count;
    return Math.max(-100, Math.min(100, Math.round(avg * 200)));
  }

  it("returns 0 for empty history", () => {
    expect(calculateMomentumFromHistory({})).toBe(0);
  });

  it("returns positive for rising prices", () => {
    const result = calculateMomentumFromHistory({
      BTC: [60000, 60500, 61000],
      ETH: [3000, 3050, 3100],
    });
    expect(result).toBeGreaterThan(0);
  });

  it("returns negative for falling prices", () => {
    const result = calculateMomentumFromHistory({
      BTC: [61000, 60500, 60000],
      ETH: [3100, 3050, 3000],
    });
    expect(result).toBeLessThan(0);
  });

  it("clamps to -100..100", () => {
    const result = calculateMomentumFromHistory({
      BTC: [50000, 55000], // +10%
    });
    expect(result).toBe(100);
  });
});

describe("Volatility from price history", () => {
  function calculateVolatilityFromHistory(
    priceHistory: Record<string, number[]>
  ): number {
    const symbols = ["BTC", "ETH", "SOL"];
    let totalCV = 0;
    let count = 0;
    for (const sym of symbols) {
      const hist = priceHistory[sym];
      if (!hist || hist.length < 3) continue;
      const mean = hist.reduce((s, v) => s + v, 0) / hist.length;
      if (mean <= 0) continue;
      const variance = hist.reduce((s, v) => s + (v - mean) ** 2, 0) / hist.length;
      const cv = Math.sqrt(variance) / mean;
      totalCV += cv;
      count++;
    }
    if (count === 0) return 30;
    const avgCV = totalCV / count;
    return Math.max(0, Math.min(100, Math.round(avgCV * 20000)));
  }

  it("returns default 30 for empty history", () => {
    expect(calculateVolatilityFromHistory({})).toBe(30);
  });

  it("returns 0 for flat prices", () => {
    const result = calculateVolatilityFromHistory({
      BTC: [60000, 60000, 60000, 60000],
    });
    expect(result).toBe(0);
  });

  it("returns higher score for volatile prices", () => {
    const flat = calculateVolatilityFromHistory({
      BTC: [60000, 60010, 60020],
    });
    const wild = calculateVolatilityFromHistory({
      BTC: [60000, 61000, 59000],
    });
    expect(wild).toBeGreaterThan(flat);
  });

  it("clamps to 0-100", () => {
    const result = calculateVolatilityFromHistory({
      BTC: [10000, 50000, 10000], // extreme swing
    });
    expect(result).toBeGreaterThanOrEqual(0);
    expect(result).toBeLessThanOrEqual(100);
  });
});
