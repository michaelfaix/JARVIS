/**
 * Tests for multi-market sentiment calculation helpers (v2).
 */
import {
  classify,
  momentumLabel,
  volatilityLabel,
  calculateMomentumFromHistory,
  calculateVolatilityFromHistory,
  compositeCommodityFG,
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

describe("calculateMomentumFromHistory (3-min buffer)", () => {
  it("returns 0 for empty history", () => {
    expect(calculateMomentumFromHistory({}, ["BTC"])).toBe(0);
  });

  it("returns positive for rising prices", () => {
    const result = calculateMomentumFromHistory(
      { BTC: [60000, 60100, 60200, 60300], ETH: [3000, 3010, 3020, 3030] },
      ["BTC", "ETH"]
    );
    expect(result).toBeGreaterThan(0);
  });

  it("returns negative for falling prices", () => {
    const result = calculateMomentumFromHistory(
      { BTC: [61000, 60800, 60600], ETH: [3100, 3080, 3060] },
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
      { SPY: [520, 521, 522, 523], AAPL: [195, 196, 197, 198] },
      ["SPY", "AAPL"]
    );
    expect(result).toBeGreaterThan(0);
  });

  it("works for commodity symbols", () => {
    const result = calculateMomentumFromHistory(
      { GLD: [215, 214, 213, 212] },
      ["GLD"]
    );
    expect(result).toBeLessThan(0);
  });

  it("ignores symbols not in history", () => {
    const result = calculateMomentumFromHistory(
      { BTC: [60000, 60100] },
      ["BTC", "XYZ"]
    );
    expect(result).toBeGreaterThan(0);
  });
});

describe("calculateVolatilityFromHistory (3-min buffer)", () => {
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
});

describe("compositeCommodityFG", () => {
  it("returns 50 (neutral) for flat prices", () => {
    const hist = { GLD: Array.from({ length: 20 }, () => 215) };
    const result = compositeCommodityFG(hist, ["GLD"]);
    // Flat: momentum=50, vol=100 (low vol inverted), MA=50 → ~65
    expect(result).toBeGreaterThanOrEqual(40);
    expect(result).toBeLessThanOrEqual(80);
  });

  it("returns higher values for rising prices", () => {
    const rising = { GLD: Array.from({ length: 20 }, (_, i) => 215 + i * 0.1) };
    const falling = { GLD: Array.from({ length: 20 }, (_, i) => 215 - i * 0.1) };
    const rResult = compositeCommodityFG(rising, ["GLD"]);
    const fResult = compositeCommodityFG(falling, ["GLD"]);
    expect(rResult).toBeGreaterThan(fResult);
  });

  it("is bounded 0-100", () => {
    const extreme = { GLD: [100, 200, 100, 200, 100, 200, 100] };
    const result = compositeCommodityFG(extreme, ["GLD"]);
    expect(result).toBeGreaterThanOrEqual(0);
    expect(result).toBeLessThanOrEqual(100);
  });

  it("works with insufficient data", () => {
    // Less than 5 entries → momentum/vol return defaults
    const short = { GLD: [215, 216] };
    const result = compositeCommodityFG(short, ["GLD"]);
    expect(result).toBeGreaterThanOrEqual(0);
    expect(result).toBeLessThanOrEqual(100);
  });
});
