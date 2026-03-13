// =============================================================================
// src/hooks/use-signals.ts — Trading Signals from JARVIS Backend
//
// Computes real technical features from priceHistory (momentum, volatility,
// trend, RSI, MACD proxy, Bollinger width, ATR proxy) and sends them to
// the backend /predict endpoint. Uses live prices for entry/SL/TP.
//
// Falls back to locally-derived signals when backend is offline.
// =============================================================================

"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { batchPredict, type AssetPrediction } from "@/lib/api";
import type { Signal } from "@/lib/types";
import { DEFAULT_ASSETS } from "@/lib/constants";
import { useSignalStream } from "./use-signal-stream";

// ---------------------------------------------------------------------------
// Technical feature computation from price history
// ---------------------------------------------------------------------------

/** Simple RSI approximation from price array (0-100) */
function computeRSI(prices: number[]): number {
  if (prices.length < 3) return 50;
  let gains = 0;
  let losses = 0;
  for (let i = 1; i < prices.length; i++) {
    const diff = prices[i] - prices[i - 1];
    if (diff > 0) gains += diff;
    else losses -= diff;
  }
  if (losses === 0) return 100;
  if (gains === 0) return 0;
  const rs = gains / losses;
  return 100 - 100 / (1 + rs);
}

/** Coefficient of variation (std/mean) */
function computeCV(prices: number[]): number {
  if (prices.length < 2) return 0;
  const mean = prices.reduce((s, v) => s + v, 0) / prices.length;
  if (mean <= 0) return 0;
  const variance =
    prices.reduce((s, v) => s + (v - mean) ** 2, 0) / prices.length;
  return Math.sqrt(variance) / mean;
}

/** Average True Range proxy from close prices (normalized by mean) */
function computeATR(prices: number[]): number {
  if (prices.length < 3) return 0;
  let totalRange = 0;
  for (let i = 1; i < prices.length; i++) {
    totalRange += Math.abs(prices[i] - prices[i - 1]);
  }
  const mean = prices.reduce((s, v) => s + v, 0) / prices.length;
  if (mean <= 0) return 0;
  return (totalRange / (prices.length - 1)) / mean;
}

/** Bollinger Band width (2σ / MA) */
function computeBBWidth(prices: number[]): number {
  if (prices.length < 5) return 0;
  const mean = prices.reduce((s, v) => s + v, 0) / prices.length;
  if (mean <= 0) return 0;
  const variance =
    prices.reduce((s, v) => s + (v - mean) ** 2, 0) / prices.length;
  return (2 * Math.sqrt(variance)) / mean;
}

/** Simple trend: linear regression slope normalized by mean */
function computeTrend(prices: number[]): number {
  if (prices.length < 3) return 0;
  const n = prices.length;
  const mean = prices.reduce((s, v) => s + v, 0) / n;
  if (mean <= 0) return 0;
  let sumXY = 0;
  let sumX2 = 0;
  const xMean = (n - 1) / 2;
  for (let i = 0; i < n; i++) {
    sumXY += (i - xMean) * prices[i];
    sumX2 += (i - xMean) ** 2;
  }
  const slope = sumX2 > 0 ? sumXY / sumX2 : 0;
  return slope / mean; // normalized slope
}

/** MACD proxy: short MA - long MA, normalized */
function computeMACD(prices: number[]): number {
  if (prices.length < 10) return 0;
  const shortLen = Math.min(12, Math.floor(prices.length / 2));
  const longLen = prices.length;
  const shortMA =
    prices.slice(-shortLen).reduce((s, v) => s + v, 0) / shortLen;
  const longMA = prices.reduce((s, v) => s + v, 0) / longLen;
  if (longMA <= 0) return 0;
  return (shortMA - longMA) / longMA;
}

/**
 * Compute real technical features from price history for a single asset.
 * All features are normalized to roughly -1..+1 or 0..1 range.
 */
function computeFeatures(
  priceHistory: Record<string, number[]>,
  symbol: string
): Record<string, number> {
  const hist = priceHistory[symbol];
  if (!hist || hist.length < 3) {
    // Not enough data — return neutral features
    return {
      momentum: 0,
      volatility: 0,
      trend: 0,
      rsi: 0,
      macd: 0,
      bb_width: 0,
      atr: 0,
    };
  }

  const first = hist[0];
  const last = hist[hist.length - 1];
  const momentum = first > 0 ? (last - first) / first : 0;
  const volatility = computeCV(hist);
  const trend = computeTrend(hist);
  const rsi = (computeRSI(hist) - 50) / 50; // normalize 0-100 → -1..+1
  const macd = computeMACD(hist);
  const bbWidth = computeBBWidth(hist);
  const atr = computeATR(hist);

  return {
    momentum: parseFloat(momentum.toFixed(6)),
    volatility: parseFloat(volatility.toFixed(6)),
    trend: parseFloat(trend.toFixed(6)),
    rsi: parseFloat(rsi.toFixed(4)),
    macd: parseFloat(macd.toFixed(6)),
    bb_width: parseFloat(bbWidth.toFixed(6)),
    atr: parseFloat(atr.toFixed(6)),
  };
}

// ---------------------------------------------------------------------------
// Local fallback signals (when backend is offline)
// ---------------------------------------------------------------------------

function localFallbackSignals(
  prices: Record<string, number>,
  priceHistory: Record<string, number[]>
): Signal[] {
  return DEFAULT_ASSETS.map((asset) => {
    const features = computeFeatures(priceHistory, asset.symbol);
    const price = prices[asset.symbol] ?? asset.price;
    const direction: "LONG" | "SHORT" =
      features.momentum >= 0 ? "LONG" : "SHORT";
    const confidence = Math.min(
      0.95,
      Math.max(0.1, 0.5 + Math.abs(features.momentum) * 50 + Math.abs(features.trend) * 200)
    );
    const vol = Math.max(0.005, features.volatility * 10);

    return {
      id: `local-${asset.symbol}-${Date.now()}`,
      asset: asset.symbol,
      direction,
      entry: price,
      stopLoss:
        direction === "LONG"
          ? price * (1 - vol * 2)
          : price * (1 + vol * 2),
      takeProfit:
        direction === "LONG"
          ? price * (1 + vol * 3)
          : price * (1 - vol * 3),
      confidence,
      qualityScore: 0,
      regime: "UNKNOWN",
      isOod: true,
      oodScore: 1,
      uncertainty: null,
      deepPathUsed: false,
      timestamp: new Date(),
    };
  }).filter((s) => s !== null);
}

// ---------------------------------------------------------------------------
// Prediction → Signal conversion
// ---------------------------------------------------------------------------

function predictionToSignal(
  ap: AssetPrediction,
  livePrice: number
): Signal | null {
  if (!ap.prediction) return null;
  const p = ap.prediction;
  const direction: "LONG" | "SHORT" = p.mu >= 0 ? "LONG" : "SHORT";
  const sigma = Math.max(p.sigma, 0.001);

  return {
    id: `${ap.asset}-${Date.now()}`,
    asset: ap.asset,
    direction,
    entry: livePrice,
    stopLoss:
      direction === "LONG"
        ? livePrice * (1 - sigma * 2)
        : livePrice * (1 + sigma * 2),
    takeProfit:
      direction === "LONG"
        ? livePrice * (1 + sigma * 3)
        : livePrice * (1 - sigma * 3),
    confidence: p.confidence,
    qualityScore: p.quality_score,
    regime: p.regime,
    isOod: p.is_ood,
    oodScore: p.ood_score,
    uncertainty: p.uncertainty,
    deepPathUsed: p.deep_path_used,
    timestamp: new Date(),
  };
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useSignals(
  regime: string = "RISK_ON",
  intervalMs: number = 10000,
  prices?: Record<string, number>,
  priceHistory?: Record<string, number[]>
) {
  const [polledSignals, setPolledSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [backendOnline, setBackendOnline] = useState(false);
  const mountedRef = useRef(true);

  // Use refs to avoid callback recreation on every price tick
  const pricesRef = useRef(prices);
  pricesRef.current = prices;
  const priceHistoryRef = useRef(priceHistory);
  priceHistoryRef.current = priceHistory;

  // WebSocket stream for real-time signals
  const symbols = useMemo(
    () => DEFAULT_ASSETS.map((a) => a.symbol),
    []
  );
  const { streamSignals, wsConnected } = useSignalStream(
    symbols,
    prices ?? {}
  );

  const refresh = useCallback(async () => {
    const ph = priceHistoryRef.current ?? {};
    const pr = pricesRef.current ?? {};

    try {
      const assets = DEFAULT_ASSETS.map((a) => ({
        symbol: a.symbol,
        features: computeFeatures(ph, a.symbol),
      }));
      const results = await batchPredict(assets, regime);
      if (!mountedRef.current) return;

      const newSignals = results
        .map((ap) => {
          const livePrice = pr[ap.asset] ?? DEFAULT_ASSETS.find(
            (a) => a.symbol === ap.asset
          )?.price ?? 0;
          return predictionToSignal(ap, livePrice);
        })
        .filter((s): s is Signal => s !== null);

      setPolledSignals(newSignals);
      setError(null);
      setBackendOnline(true);
    } catch (err) {
      if (!mountedRef.current) return;

      // Fallback: generate local signals from price data
      const fallback = localFallbackSignals(pr, ph);
      setPolledSignals(fallback);
      setBackendOnline(false);
      setError(err instanceof Error ? err.message : "Backend offline");
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, [regime]); // Only depends on regime — prices via refs

  useEffect(() => {
    mountedRef.current = true;
    refresh();
    const id = setInterval(refresh, intervalMs);
    return () => {
      mountedRef.current = false;
      clearInterval(id);
    };
  }, [refresh, intervalMs]);

  // Merge: WS stream signals override polled signals for the same asset
  const signals = useMemo(() => {
    if (streamSignals.length === 0) return polledSignals;

    const wsMap = new Map(streamSignals.map((s) => [s.asset, s]));
    const merged = polledSignals.map((s) => wsMap.get(s.asset) ?? s);

    // Add any WS signals for assets not in polled set
    for (const ws of streamSignals) {
      if (!polledSignals.some((p) => p.asset === ws.asset)) {
        merged.push(ws);
      }
    }
    return merged;
  }, [polledSignals, streamSignals]);

  return { signals, loading, error, backendOnline, wsConnected, refresh };
}
