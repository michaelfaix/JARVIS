// =============================================================================
// Tests: lib/indicators.ts — Pure technical analysis calculations
// =============================================================================

import {
  calcSMA,
  calcEMA,
  calcRSI,
  calcMACD,
  calcBollingerBands,
} from "@/lib/indicators";

// Helper to create candle data from close prices
function candles(closes: number[]): { close: number }[] {
  return closes.map((close) => ({ close }));
}

describe("calcSMA", () => {
  it("returns all nulls when data length < period", () => {
    const result = calcSMA(candles([10, 20]), 5);
    expect(result).toEqual([null, null]);
  });

  it("returns all nulls when period <= 0", () => {
    const result = calcSMA(candles([10, 20, 30]), 0);
    expect(result).toEqual([null, null, null]);
  });

  it("calculates SMA correctly for period=3", () => {
    const data = candles([10, 20, 30, 40, 50]);
    const result = calcSMA(data, 3);

    expect(result[0]).toBeNull();
    expect(result[1]).toBeNull();
    expect(result[2]).toBeCloseTo(20, 5); // (10+20+30)/3
    expect(result[3]).toBeCloseTo(30, 5); // (20+30+40)/3
    expect(result[4]).toBeCloseTo(40, 5); // (30+40+50)/3
  });

  it("handles period=1 (returns raw values)", () => {
    const data = candles([5, 10, 15]);
    const result = calcSMA(data, 1);

    expect(result[0]).toBeCloseTo(5);
    expect(result[1]).toBeCloseTo(10);
    expect(result[2]).toBeCloseTo(15);
  });

  it("handles constant values", () => {
    const data = candles([100, 100, 100, 100, 100]);
    const result = calcSMA(data, 3);

    expect(result[2]).toBeCloseTo(100);
    expect(result[3]).toBeCloseTo(100);
    expect(result[4]).toBeCloseTo(100);
  });

  it("result length matches input length", () => {
    const data = candles([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
    const result = calcSMA(data, 3);
    expect(result).toHaveLength(10);
  });
});

describe("calcEMA", () => {
  it("returns all nulls when data length < period", () => {
    const result = calcEMA(candles([10, 20]), 5);
    expect(result).toEqual([null, null]);
  });

  it("returns all nulls when period <= 0", () => {
    const result = calcEMA(candles([10, 20, 30]), -1);
    expect(result).toEqual([null, null, null]);
  });

  it("first EMA value equals SMA (seed)", () => {
    const data = candles([10, 20, 30, 40, 50]);
    const ema = calcEMA(data, 3);
    const sma = calcSMA(data, 3);

    // At index 2 (period-1), EMA seed = SMA
    expect(ema[2]).toBeCloseTo(sma[2]!, 5);
  });

  it("subsequent EMA values use exponential smoothing", () => {
    const data = candles([10, 20, 30, 40, 50]);
    const result = calcEMA(data, 3);

    // k = 2/(3+1) = 0.5
    // EMA[2] = SMA = 20
    // EMA[3] = 40 * 0.5 + 20 * 0.5 = 30
    expect(result[3]).toBeCloseTo(30, 5);
    // EMA[4] = 50 * 0.5 + 30 * 0.5 = 40
    expect(result[4]).toBeCloseTo(40, 5);
  });

  it("result length matches input length", () => {
    const data = candles([1, 2, 3, 4, 5]);
    const result = calcEMA(data, 3);
    expect(result).toHaveLength(5);
  });

  it("handles period=1", () => {
    const data = candles([5, 10, 15]);
    const result = calcEMA(data, 1);
    // k = 2/2 = 1, so EMA always equals current value
    expect(result[0]).toBeCloseTo(5);
    expect(result[1]).toBeCloseTo(10);
    expect(result[2]).toBeCloseTo(15);
  });
});

describe("calcRSI", () => {
  it("returns all nulls when insufficient data", () => {
    const result = calcRSI(candles([10, 20]), 14);
    expect(result.every((v) => v === null)).toBe(true);
  });

  it("returns all nulls when period <= 0", () => {
    const result = calcRSI(candles([10, 20, 30]), 0);
    expect(result.every((v) => v === null)).toBe(true);
  });

  it("returns 100 when all changes are positive", () => {
    // Monotonically increasing: all gains, zero losses
    const data = candles([10, 11, 12, 13, 14, 15]);
    const result = calcRSI(data, 4);
    // avgLoss = 0, so RSI = 100
    const nonNull = result.filter((v) => v !== null);
    expect(nonNull.length).toBeGreaterThan(0);
    for (const v of nonNull) {
      expect(v).toBe(100);
    }
  });

  it("RSI values are between 0 and 100", () => {
    const data = candles([44, 44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.1, 45.42, 45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28, 46.00, 46.03, 46.41, 46.22, 45.64]);
    const result = calcRSI(data, 14);

    for (const v of result) {
      if (v !== null) {
        expect(v).toBeGreaterThanOrEqual(0);
        expect(v).toBeLessThanOrEqual(100);
      }
    }
  });

  it("result length matches input length", () => {
    const data = candles([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
    const result = calcRSI(data, 3);
    expect(result).toHaveLength(10);
  });

  it("first period entries are null", () => {
    const data = candles([10, 11, 12, 13, 14, 15, 16, 17]);
    const result = calcRSI(data, 5);
    // First 5 entries (indices 0-4) should be null
    for (let i = 0; i < 5; i++) {
      expect(result[i]).toBeNull();
    }
    expect(result[5]).not.toBeNull();
  });
});

describe("calcMACD", () => {
  it("returns all nulls when data length < slow period", () => {
    const data = candles(Array.from({ length: 20 }, (_, i) => 100 + i));
    const result = calcMACD(data, 12, 26, 9);

    expect(result.macd.every((v) => v === null)).toBe(true);
    expect(result.signal.every((v) => v === null)).toBe(true);
    expect(result.histogram.every((v) => v === null)).toBe(true);
  });

  it("returns three arrays of equal length", () => {
    const data = candles(Array.from({ length: 50 }, (_, i) => 100 + Math.sin(i) * 10));
    const result = calcMACD(data);

    expect(result.macd).toHaveLength(50);
    expect(result.signal).toHaveLength(50);
    expect(result.histogram).toHaveLength(50);
  });

  it("MACD line starts from slow period - 1", () => {
    const data = candles(Array.from({ length: 50 }, (_, i) => 100 + i));
    const result = calcMACD(data, 12, 26, 9);

    // First 25 MACD values should be null (slow=26, so first non-null at index 25)
    for (let i = 0; i < 25; i++) {
      expect(result.macd[i]).toBeNull();
    }
    expect(result.macd[25]).not.toBeNull();
  });

  it("histogram = MACD - signal", () => {
    const data = candles(Array.from({ length: 60 }, (_, i) => 100 + Math.sin(i / 5) * 20));
    const result = calcMACD(data, 12, 26, 9);

    for (let i = 0; i < data.length; i++) {
      if (result.histogram[i] !== null && result.macd[i] !== null && result.signal[i] !== null) {
        expect(result.histogram[i]).toBeCloseTo(
          result.macd[i]! - result.signal[i]!,
          8
        );
      }
    }
  });
});

describe("calcBollingerBands", () => {
  it("returns all nulls when data length < period", () => {
    const data = candles([10, 20, 30]);
    const result = calcBollingerBands(data, 20, 2);

    expect(result.upper.every((v) => v === null)).toBe(true);
    expect(result.lower.every((v) => v === null)).toBe(true);
  });

  it("middle band equals SMA", () => {
    const data = candles(Array.from({ length: 30 }, (_, i) => 100 + i));
    const result = calcBollingerBands(data, 20, 2);
    const sma = calcSMA(data, 20);

    for (let i = 0; i < data.length; i++) {
      if (result.middle[i] !== null) {
        expect(result.middle[i]).toBeCloseTo(sma[i]!, 8);
      }
    }
  });

  it("upper > middle > lower when there is variance", () => {
    const data = candles(Array.from({ length: 25 }, (_, i) => 100 + (i % 5) * 3));
    const result = calcBollingerBands(data, 20, 2);

    for (let i = 19; i < data.length; i++) {
      expect(result.upper[i]!).toBeGreaterThan(result.middle[i]!);
      expect(result.middle[i]!).toBeGreaterThan(result.lower[i]!);
    }
  });

  it("bands collapse to SMA when all values are equal", () => {
    const data = candles(Array(25).fill(100));
    const result = calcBollingerBands(data, 20, 2);

    for (let i = 19; i < data.length; i++) {
      expect(result.upper[i]).toBeCloseTo(100, 5);
      expect(result.middle[i]).toBeCloseTo(100, 5);
      expect(result.lower[i]).toBeCloseTo(100, 5);
    }
  });

  it("returns three arrays of correct length", () => {
    const data = candles(Array.from({ length: 50 }, () => Math.random() * 100));
    const result = calcBollingerBands(data, 20, 2);

    expect(result.upper).toHaveLength(50);
    expect(result.middle).toHaveLength(50);
    expect(result.lower).toHaveLength(50);
  });

  it("respects custom stdDev multiplier", () => {
    const data = candles(Array.from({ length: 25 }, (_, i) => 100 + i));
    const narrow = calcBollingerBands(data, 20, 1);
    const wide = calcBollingerBands(data, 20, 3);

    // Wider stdDev = bigger distance from middle
    for (let i = 19; i < data.length; i++) {
      const narrowWidth = narrow.upper[i]! - narrow.lower[i]!;
      const wideWidth = wide.upper[i]! - wide.lower[i]!;
      expect(wideWidth).toBeGreaterThan(narrowWidth);
    }
  });
});
