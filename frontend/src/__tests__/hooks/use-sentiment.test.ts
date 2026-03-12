/**
 * Tests for multi-market sentiment calculation helpers.
 */
import {
  classify,
  momentumLabel,
  volatilityLabel,
  calculateMomentumFromHistory,
  calculateVolatilityFromHistory,
} from "@/hooks/use-sentiment";

describe("classify", () => {
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
});

describe("momentumLabel", () => {
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
});

describe("volatilityLabel", () => {
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

describe("calculateMomentumFromHistory", () => {
  it("returns 0 for empty history", () => {
    expect(calculateMomentumFromHistory({}, ["BTC"])).toBe(0);
  });

  it("returns positive for rising prices", () => {
    const result = calculateMomentumFromHistory(
      { BTC: [60000, 60500, 61000], ETH: [3000, 3050, 3100] },
      ["BTC", "ETH"]
    );
    expect(result).toBeGreaterThan(0);
  });

  it("returns negative for falling prices", () => {
    const result = calculateMomentumFromHistory(
      { BTC: [61000, 60500, 60000], ETH: [3100, 3050, 3000] },
      ["BTC", "ETH"]
    );
    expect(result).toBeLessThan(0);
  });

  it("clamps to ±100", () => {
    const result = calculateMomentumFromHistory(
      { BTC: [50000, 55000] },
      ["BTC"]
    );
    expect(result).toBe(100);
  });

  it("works for stock symbols", () => {
    const result = calculateMomentumFromHistory(
      { SPY: [520, 525, 530], AAPL: [195, 197, 199] },
      ["SPY", "AAPL"]
    );
    expect(result).toBeGreaterThan(0);
  });

  it("works for commodity symbols", () => {
    const result = calculateMomentumFromHistory(
      { GLD: [215, 213, 211] },
      ["GLD"]
    );
    expect(result).toBeLessThan(0);
  });
});

describe("calculateVolatilityFromHistory", () => {
  it("returns default 30 for empty history", () => {
    expect(calculateVolatilityFromHistory({}, ["BTC"])).toBe(30);
  });

  it("returns 0 for flat prices", () => {
    const result = calculateVolatilityFromHistory(
      { BTC: [60000, 60000, 60000, 60000] },
      ["BTC"]
    );
    expect(result).toBe(0);
  });

  it("returns higher score for volatile prices", () => {
    const flat = calculateVolatilityFromHistory(
      { BTC: [60000, 60010, 60020] },
      ["BTC"]
    );
    const wild = calculateVolatilityFromHistory(
      { BTC: [60000, 61000, 59000] },
      ["BTC"]
    );
    expect(wild).toBeGreaterThan(flat);
  });

  it("clamps to 0-100", () => {
    const result = calculateVolatilityFromHistory(
      { BTC: [10000, 50000, 10000] },
      ["BTC"]
    );
    expect(result).toBeGreaterThanOrEqual(0);
    expect(result).toBeLessThanOrEqual(100);
  });

  it("works across multiple symbol groups", () => {
    const result = calculateVolatilityFromHistory(
      { SPY: [520, 521, 519, 522], NVDA: [890, 895, 885, 900] },
      ["SPY", "NVDA"]
    );
    expect(result).toBeGreaterThanOrEqual(0);
  });
});
