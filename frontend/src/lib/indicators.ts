// =============================================================================
// src/lib/indicators.ts — Pure Technical Analysis Indicator Calculations
//
// No React, no side effects. Each function takes candle data and returns
// computed indicator values aligned by index with the input array.
// Positions where there is insufficient data return null.
// =============================================================================

/**
 * Simple Moving Average
 * Returns an array of SMA values aligned with input data.
 * First (period - 1) entries are null.
 */
export function calcSMA(
  data: { close: number }[],
  period: number
): (number | null)[] {
  const result: (number | null)[] = new Array(data.length).fill(null);
  if (period <= 0 || data.length < period) return result;

  let sum = 0;
  for (let i = 0; i < period; i++) {
    sum += data[i].close;
  }
  result[period - 1] = sum / period;

  for (let i = period; i < data.length; i++) {
    sum += data[i].close - data[i - period].close;
    result[i] = sum / period;
  }

  return result;
}

/**
 * Exponential Moving Average
 * Uses SMA of the first `period` values as the initial EMA seed.
 * First (period - 1) entries are null.
 */
export function calcEMA(
  data: { close: number }[],
  period: number
): (number | null)[] {
  const result: (number | null)[] = new Array(data.length).fill(null);
  if (period <= 0 || data.length < period) return result;

  const k = 2 / (period + 1);

  // Seed with SMA of first `period` values
  let sum = 0;
  for (let i = 0; i < period; i++) {
    sum += data[i].close;
  }
  let ema = sum / period;
  result[period - 1] = ema;

  for (let i = period; i < data.length; i++) {
    ema = data[i].close * k + ema * (1 - k);
    result[i] = ema;
  }

  return result;
}

/**
 * Relative Strength Index (0-100)
 * Uses Wilder's smoothing method. First `period` entries are null.
 */
export function calcRSI(
  data: { close: number }[],
  period: number
): (number | null)[] {
  const result: (number | null)[] = new Array(data.length).fill(null);
  if (period <= 0 || data.length < period + 1) return result;

  // Calculate price changes
  const changes: number[] = [];
  for (let i = 1; i < data.length; i++) {
    changes.push(data[i].close - data[i - 1].close);
  }

  // Initial average gain/loss over first `period` changes
  let avgGain = 0;
  let avgLoss = 0;
  for (let i = 0; i < period; i++) {
    if (changes[i] >= 0) {
      avgGain += changes[i];
    } else {
      avgLoss += Math.abs(changes[i]);
    }
  }
  avgGain /= period;
  avgLoss /= period;

  // RSI at index (period) in the original data (changes index period - 1)
  const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
  result[period] = avgLoss === 0 ? 100 : 100 - 100 / (1 + rs);

  // Wilder's smoothing for subsequent values
  for (let i = period; i < changes.length; i++) {
    const gain = changes[i] >= 0 ? changes[i] : 0;
    const loss = changes[i] < 0 ? Math.abs(changes[i]) : 0;

    avgGain = (avgGain * (period - 1) + gain) / period;
    avgLoss = (avgLoss * (period - 1) + loss) / period;

    const rsI = avgLoss === 0 ? 100 : avgGain / avgLoss;
    result[i + 1] = avgLoss === 0 ? 100 : 100 - 100 / (1 + rsI);
  }

  return result;
}

/**
 * MACD — Moving Average Convergence Divergence
 * Returns three arrays: macd line, signal line, and histogram.
 */
export function calcMACD(
  data: { close: number }[],
  fast: number = 12,
  slow: number = 26,
  signal: number = 9
): {
  macd: (number | null)[];
  signal: (number | null)[];
  histogram: (number | null)[];
} {
  const len = data.length;
  const macdLine: (number | null)[] = new Array(len).fill(null);
  const signalLine: (number | null)[] = new Array(len).fill(null);
  const histogram: (number | null)[] = new Array(len).fill(null);

  if (len < slow) return { macd: macdLine, signal: signalLine, histogram };

  const fastEMA = calcEMA(data, fast);
  const slowEMA = calcEMA(data, slow);

  // MACD line = fast EMA - slow EMA (available from index slow - 1)
  const macdValues: { close: number }[] = [];
  let macdStart = -1;

  for (let i = 0; i < len; i++) {
    if (fastEMA[i] !== null && slowEMA[i] !== null) {
      const val = fastEMA[i]! - slowEMA[i]!;
      macdLine[i] = val;
      macdValues.push({ close: val });
      if (macdStart === -1) macdStart = i;
    }
  }

  // Signal line = EMA of MACD values
  if (macdValues.length >= signal) {
    const sigEMA = calcEMA(macdValues, signal);
    for (let j = 0; j < sigEMA.length; j++) {
      const dataIdx = macdStart + j;
      if (sigEMA[j] !== null) {
        signalLine[dataIdx] = sigEMA[j];
        histogram[dataIdx] = macdLine[dataIdx]! - sigEMA[j]!;
      }
    }
  }

  return { macd: macdLine, signal: signalLine, histogram };
}

/**
 * Bollinger Bands
 * Returns upper, middle (SMA), and lower bands.
 */
export function calcBollingerBands(
  data: { close: number }[],
  period: number = 20,
  stdDev: number = 2
): {
  upper: (number | null)[];
  middle: (number | null)[];
  lower: (number | null)[];
} {
  const len = data.length;
  const upper: (number | null)[] = new Array(len).fill(null);
  const lower: (number | null)[] = new Array(len).fill(null);

  const middle = calcSMA(data, period);

  for (let i = period - 1; i < len; i++) {
    const sma = middle[i]!;
    let sumSq = 0;
    for (let j = i - period + 1; j <= i; j++) {
      const diff = data[j].close - sma;
      sumSq += diff * diff;
    }
    const sd = Math.sqrt(sumSq / period);
    upper[i] = sma + stdDev * sd;
    lower[i] = sma - stdDev * sd;
  }

  return { upper, middle, lower };
}
