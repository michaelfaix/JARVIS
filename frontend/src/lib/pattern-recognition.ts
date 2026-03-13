// =============================================================================
// src/lib/pattern-recognition.ts — Chart Pattern Detection
//
// Detects: Support/Resistance, Double Bottom/Top, Head & Shoulders,
// Bull/Bear Flags, Triangles from OHLC candle data.
// =============================================================================

interface Candle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface PatternResult {
  type: string;
  confidence: number;
  description: string;
  priceLevel?: number;
}

export interface SupportResistance {
  support: number[];
  resistance: number[];
}

// ---------------------------------------------------------------------------
// Pivot detection helpers
// ---------------------------------------------------------------------------

function findPivotHighs(candles: Candle[], lookback: number = 5): { index: number; price: number }[] {
  const pivots: { index: number; price: number }[] = [];
  for (let i = lookback; i < candles.length - lookback; i++) {
    let isPivot = true;
    for (let j = 1; j <= lookback; j++) {
      if (candles[i].high <= candles[i - j].high || candles[i].high <= candles[i + j].high) {
        isPivot = false;
        break;
      }
    }
    if (isPivot) pivots.push({ index: i, price: candles[i].high });
  }
  return pivots;
}

function findPivotLows(candles: Candle[], lookback: number = 5): { index: number; price: number }[] {
  const pivots: { index: number; price: number }[] = [];
  for (let i = lookback; i < candles.length - lookback; i++) {
    let isPivot = true;
    for (let j = 1; j <= lookback; j++) {
      if (candles[i].low >= candles[i - j].low || candles[i].low >= candles[i + j].low) {
        isPivot = false;
        break;
      }
    }
    if (isPivot) pivots.push({ index: i, price: candles[i].low });
  }
  return pivots;
}

function pricesNear(a: number, b: number, tolerance: number = 0.02): boolean {
  return Math.abs(a - b) / Math.max(a, b) < tolerance;
}

// ---------------------------------------------------------------------------
// Support & Resistance
// ---------------------------------------------------------------------------

export function detectSupportResistance(candles: Candle[]): SupportResistance {
  if (candles.length < 20) return { support: [], resistance: [] };

  const highs = findPivotHighs(candles, 3);
  const lows = findPivotLows(candles, 3);

  // Cluster nearby levels
  const clusterLevels = (pivots: { price: number }[]): number[] => {
    if (pivots.length === 0) return [];
    const sorted = [...pivots].sort((a, b) => a.price - b.price);
    const clusters: number[][] = [[sorted[0].price]];
    for (let i = 1; i < sorted.length; i++) {
      const lastCluster = clusters[clusters.length - 1];
      const avgPrice = lastCluster.reduce((s, p) => s + p, 0) / lastCluster.length;
      if (pricesNear(sorted[i].price, avgPrice, 0.015)) {
        lastCluster.push(sorted[i].price);
      } else {
        clusters.push([sorted[i].price]);
      }
    }
    // Return average of clusters with at least 2 touches
    return clusters
      .filter((c) => c.length >= 2)
      .map((c) => c.reduce((s, p) => s + p, 0) / c.length)
      .slice(-3); // Top 3
  };

  return {
    support: clusterLevels(lows),
    resistance: clusterLevels(highs),
  };
}

// ---------------------------------------------------------------------------
// Double Bottom
// ---------------------------------------------------------------------------

function detectDoubleBottom(candles: Candle[]): PatternResult | null {
  const lows = findPivotLows(candles, 3);
  if (lows.length < 2) return null;

  // Check last two lows
  const l1 = lows[lows.length - 2];
  const l2 = lows[lows.length - 1];

  if (l2.index - l1.index < 5) return null; // Too close
  if (!pricesNear(l1.price, l2.price, 0.025)) return null; // Prices must be similar

  // Confirm: price between the lows should be higher (the neckline)
  let neckline = 0;
  for (let i = l1.index; i <= l2.index; i++) {
    neckline = Math.max(neckline, candles[i].high);
  }
  if (neckline <= l1.price * 1.02) return null;

  const avgLevel = (l1.price + l2.price) / 2;
  return {
    type: "Double Bottom",
    confidence: 0.7,
    description: `Double Bottom at $${avgLevel.toFixed(2)} — bullish reversal pattern`,
    priceLevel: avgLevel,
  };
}

// ---------------------------------------------------------------------------
// Double Top
// ---------------------------------------------------------------------------

function detectDoubleTop(candles: Candle[]): PatternResult | null {
  const highs = findPivotHighs(candles, 3);
  if (highs.length < 2) return null;

  const h1 = highs[highs.length - 2];
  const h2 = highs[highs.length - 1];

  if (h2.index - h1.index < 5) return null;
  if (!pricesNear(h1.price, h2.price, 0.025)) return null;

  let neckline = Infinity;
  for (let i = h1.index; i <= h2.index; i++) {
    neckline = Math.min(neckline, candles[i].low);
  }
  if (neckline >= h1.price * 0.98) return null;

  const avgLevel = (h1.price + h2.price) / 2;
  return {
    type: "Double Top",
    confidence: 0.7,
    description: `Double Top at $${avgLevel.toFixed(2)} — bearish reversal pattern`,
    priceLevel: avgLevel,
  };
}

// ---------------------------------------------------------------------------
// Head & Shoulders
// ---------------------------------------------------------------------------

function detectHeadAndShoulders(candles: Candle[]): PatternResult | null {
  const highs = findPivotHighs(candles, 3);
  if (highs.length < 3) return null;

  const [ls, head, rs] = highs.slice(-3);
  if (head.price <= ls.price || head.price <= rs.price) return null;
  if (!pricesNear(ls.price, rs.price, 0.04)) return null;
  if (head.index - ls.index < 3 || rs.index - head.index < 3) return null;

  return {
    type: "Head & Shoulders",
    confidence: 0.65,
    description: `Head & Shoulders: Head at $${head.price.toFixed(2)}, shoulders at ~$${((ls.price + rs.price) / 2).toFixed(2)} — bearish`,
    priceLevel: (ls.price + rs.price) / 2,
  };
}

// ---------------------------------------------------------------------------
// Bull/Bear Flag
// ---------------------------------------------------------------------------

function detectBullFlag(candles: Candle[]): PatternResult | null {
  if (candles.length < 20) return null;
  const recent = candles.slice(-20);

  // Check for strong uptrend in first half
  const midpoint = 10;
  const firstHalf = recent.slice(0, midpoint);
  const secondHalf = recent.slice(midpoint);

  const trendChange = (firstHalf[firstHalf.length - 1].close - firstHalf[0].close) / firstHalf[0].close;
  if (trendChange < 0.03) return null; // Need >3% uptrend

  // Second half should consolidate (lower highs, higher lows)
  const sh_highs = secondHalf.map((c) => c.high);
  const sh_lows = secondHalf.map((c) => c.low);
  const highRange = (Math.max(...sh_highs) - Math.min(...sh_highs)) / Math.max(...sh_highs);
  const lowRange = (Math.max(...sh_lows) - Math.min(...sh_lows)) / Math.max(...sh_lows);

  if (highRange > 0.04 || lowRange > 0.04) return null;

  return {
    type: "Bull Flag",
    confidence: 0.6,
    description: `Bull Flag — strong uptrend followed by consolidation. Bullish continuation expected.`,
  };
}

function detectBearFlag(candles: Candle[]): PatternResult | null {
  if (candles.length < 20) return null;
  const recent = candles.slice(-20);

  const midpoint = 10;
  const firstHalf = recent.slice(0, midpoint);
  const secondHalf = recent.slice(midpoint);

  const trendChange = (firstHalf[firstHalf.length - 1].close - firstHalf[0].close) / firstHalf[0].close;
  if (trendChange > -0.03) return null;

  const sh_highs = secondHalf.map((c) => c.high);
  const sh_lows = secondHalf.map((c) => c.low);
  const highRange = (Math.max(...sh_highs) - Math.min(...sh_highs)) / Math.max(...sh_highs);
  const lowRange = (Math.max(...sh_lows) - Math.min(...sh_lows)) / Math.max(...sh_lows);

  if (highRange > 0.04 || lowRange > 0.04) return null;

  return {
    type: "Bear Flag",
    confidence: 0.6,
    description: `Bear Flag — strong downtrend followed by consolidation. Bearish continuation expected.`,
  };
}

// ---------------------------------------------------------------------------
// Triangle
// ---------------------------------------------------------------------------

function detectTriangle(candles: Candle[]): PatternResult | null {
  if (candles.length < 20) return null;

  const recent = candles.slice(-20);
  const highs = recent.map((c) => c.high);
  const lows = recent.map((c) => c.low);

  // Check if highs are descending and lows are ascending (symmetrical triangle)
  const firstHighs = highs.slice(0, 10);
  const lastHighs = highs.slice(10);
  const firstLows = lows.slice(0, 10);
  const lastLows = lows.slice(10);

  const avgFirstHigh = firstHighs.reduce((s, v) => s + v, 0) / firstHighs.length;
  const avgLastHigh = lastHighs.reduce((s, v) => s + v, 0) / lastHighs.length;
  const avgFirstLow = firstLows.reduce((s, v) => s + v, 0) / firstLows.length;
  const avgLastLow = lastLows.reduce((s, v) => s + v, 0) / lastLows.length;

  const highsDescending = avgLastHigh < avgFirstHigh * 0.99;
  const lowsAscending = avgLastLow > avgFirstLow * 1.01;

  if (!highsDescending || !lowsAscending) return null;

  return {
    type: "Triangle",
    confidence: 0.55,
    description: `Symmetrical Triangle — price converging. Breakout imminent in either direction.`,
  };
}

// ---------------------------------------------------------------------------
// Main detection function
// ---------------------------------------------------------------------------

export function detectAllPatterns(candles: Candle[]): PatternResult[] {
  if (candles.length < 20) return [];

  const patterns: PatternResult[] = [];
  const sr = detectSupportResistance(candles);

  // Add S/R as patterns
  for (const s of sr.support) {
    patterns.push({
      type: "Support",
      confidence: 0.8,
      description: `Support level at $${s.toFixed(2)}`,
      priceLevel: s,
    });
  }
  for (const r of sr.resistance) {
    patterns.push({
      type: "Resistance",
      confidence: 0.8,
      description: `Resistance level at $${r.toFixed(2)}`,
      priceLevel: r,
    });
  }

  // Chart patterns
  const detectors = [detectDoubleBottom, detectDoubleTop, detectHeadAndShoulders, detectBullFlag, detectBearFlag, detectTriangle];
  for (const detect of detectors) {
    const result = detect(candles);
    if (result) patterns.push(result);
  }

  // Sort by confidence
  patterns.sort((a, b) => b.confidence - a.confidence);
  return patterns;
}
