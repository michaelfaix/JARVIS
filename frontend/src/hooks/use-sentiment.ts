// =============================================================================
// src/hooks/use-sentiment.ts — Market Sentiment & Fear/Greed Index
//
// Fear & Greed: Real data from alternative.me (7-day history).
// BTC Dominance: Real data from CoinGecko /global.
// Momentum & Volatility: Derived from priceHistory ring buffer.
// =============================================================================

"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

export interface SentimentData {
  value: number; // 0-100
  classification: string;
  timestamp: string;
  history: number[]; // last 7 days F&G values (oldest→newest)
  loading: boolean;
  error: string | null;
}

export interface MarketMomentum {
  score: number; // -100 to +100
  label: "Strong Bearish" | "Bearish" | "Neutral" | "Bullish" | "Strong Bullish";
}

export interface VolatilityLevel {
  score: number; // 0-100
  label: "Low" | "Medium" | "High";
}

export interface BtcDominance {
  value: number | null; // e.g. 57.3
  trend: "rising" | "falling" | "stable";
}

export interface SentimentResult {
  sentiment: SentimentData;
  momentum: MarketMomentum;
  volatility: VolatilityLevel;
  btcDominance: BtcDominance;
}

function classify(value: number): string {
  if (value <= 25) return "Extreme Fear";
  if (value <= 45) return "Fear";
  if (value <= 55) return "Neutral";
  if (value <= 75) return "Greed";
  return "Extreme Greed";
}

function momentumLabel(score: number): MarketMomentum["label"] {
  if (score <= -50) return "Strong Bearish";
  if (score <= -15) return "Bearish";
  if (score <= 15) return "Neutral";
  if (score <= 50) return "Bullish";
  return "Strong Bullish";
}

function volatilityLabel(score: number): VolatilityLevel["label"] {
  if (score < 33) return "Low";
  if (score < 66) return "Medium";
  return "High";
}

/**
 * Calculate momentum from price history buffer.
 * Compares earliest to latest prices for BTC, ETH, SOL.
 */
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
  // Map ±0.5% (typical for ring buffer window ~60s) to ±100
  return Math.max(-100, Math.min(100, Math.round(avg * 200)));
}

/**
 * Calculate volatility from price history buffer.
 * Uses coefficient of variation (stddev/mean) of recent prices.
 */
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
    const variance =
      hist.reduce((s, v) => s + (v - mean) ** 2, 0) / hist.length;
    const cv = Math.sqrt(variance) / mean;
    totalCV += cv;
    count++;
  }

  if (count === 0) return 30;
  const avgCV = totalCV / count;
  // Map CV 0–0.005 (0.5%) to 0-100
  return Math.max(0, Math.min(100, Math.round(avgCV * 20000)));
}

const POLL_INTERVAL = 5 * 60 * 1000; // 5 minutes

export function useSentiment(
  prices: Record<string, number>,
  priceHistory?: Record<string, number[]>
): SentimentResult {
  const [sentiment, setSentiment] = useState<SentimentData>({
    value: 50,
    classification: "Neutral",
    timestamp: new Date().toISOString(),
    history: [],
    loading: true,
    error: null,
  });

  const [btcDominance, setBtcDominance] = useState<BtcDominance>({
    value: null,
    trend: "stable",
  });

  const mountedRef = useRef(true);
  const prevDominanceRef = useRef<number | null>(null);

  // --- Fetch Fear & Greed (7-day history) ---
  const fetchSentiment = useCallback(async () => {
    if (!mountedRef.current) return;

    try {
      const res = await fetch("https://api.alternative.me/fng/?limit=7", {
        signal: AbortSignal.timeout(5000),
      });
      if (!res.ok) throw new Error(`API ${res.status}`);
      const json = await res.json();
      const entries = json?.data;

      if (!entries || !Array.isArray(entries) || entries.length === 0) {
        throw new Error("Invalid response");
      }

      const latest = entries[0];
      const value = parseInt(latest.value, 10);
      if (isNaN(value)) throw new Error("Invalid value");

      // History: entries are newest-first, reverse to oldest-first
      const history = entries
        .map((e: { value: string }) => parseInt(e.value, 10))
        .filter((v: number) => !isNaN(v))
        .reverse();

      if (mountedRef.current) {
        setSentiment({
          value,
          classification:
            latest.value_classification || classify(value),
          timestamp: latest.timestamp
            ? new Date(parseInt(latest.timestamp, 10) * 1000).toISOString()
            : new Date().toISOString(),
          history,
          loading: false,
          error: null,
        });
      }
    } catch (err) {
      if (!mountedRef.current) return;
      // Fallback: synthetic from prices
      const btc = prices.BTC ?? 0;
      const synth = btc > 0 ? Math.min(100, Math.max(0, Math.round(((btc % 1000) / 1000) * 100))) : 50;
      setSentiment((prev) => ({
        ...prev,
        value: synth,
        classification: classify(synth),
        timestamp: new Date().toISOString(),
        loading: false,
        error: err instanceof Error ? err.message : "API unavailable",
      }));
    }
  }, [prices]);

  // --- Fetch BTC Dominance from CoinGecko ---
  const fetchDominance = useCallback(async () => {
    if (!mountedRef.current) return;

    try {
      const res = await fetch(
        "https://api.coingecko.com/api/v3/global",
        { signal: AbortSignal.timeout(5000) }
      );
      if (!res.ok) throw new Error(`CoinGecko ${res.status}`);
      const json = await res.json();
      const dom = json?.data?.market_cap_percentage?.btc;

      if (typeof dom !== "number") throw new Error("No BTC dominance data");

      if (mountedRef.current) {
        const rounded = Math.round(dom * 10) / 10;
        const prev = prevDominanceRef.current;
        const trend: BtcDominance["trend"] =
          prev === null
            ? "stable"
            : rounded - prev > 0.2
              ? "rising"
              : rounded - prev < -0.2
                ? "falling"
                : "stable";
        prevDominanceRef.current = rounded;
        setBtcDominance({ value: rounded, trend });
      }
    } catch {
      // Keep previous value or stay at default
    }
  }, []);

  // --- Poll APIs ---
  useEffect(() => {
    mountedRef.current = true;
    fetchSentiment();
    fetchDominance();

    const id = setInterval(() => {
      fetchSentiment();
      fetchDominance();
    }, POLL_INTERVAL);

    return () => {
      mountedRef.current = false;
      clearInterval(id);
    };
  }, [fetchSentiment, fetchDominance]);

  // --- Derived metrics from priceHistory ---
  const momentum = useMemo<MarketMomentum>(() => {
    const score = priceHistory
      ? calculateMomentumFromHistory(priceHistory)
      : 0;
    return { score, label: momentumLabel(score) };
  }, [priceHistory]);

  const volatility = useMemo<VolatilityLevel>(() => {
    const score = priceHistory
      ? calculateVolatilityFromHistory(priceHistory)
      : 30;
    return { score, label: volatilityLabel(score) };
  }, [priceHistory]);

  return {
    sentiment,
    momentum,
    volatility,
    btcDominance,
  };
}
