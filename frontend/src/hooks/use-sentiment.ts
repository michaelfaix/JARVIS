// =============================================================================
// src/hooks/use-sentiment.ts — Market Sentiment & Fear/Greed Index
//
// Fetches the Crypto Fear & Greed Index from alternative.me.
// Fallback: synthetic sentiment derived from recent price movements.
// Also calculates market momentum and volatility from BTC/ETH/SOL prices.
// =============================================================================

"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export interface SentimentData {
  value: number; // 0-100
  classification: string;
  timestamp: string;
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

export interface SentimentResult {
  sentiment: SentimentData;
  momentum: MarketMomentum;
  volatility: VolatilityLevel;
  btcDominanceTrend: "rising" | "falling" | "stable";
}

function classify(value: number): string {
  if (value <= 25) return "Extreme Fear";
  if (value <= 45) return "Fear";
  if (value <= 55) return "Neutral";
  if (value <= 75) return "Greed";
  return "Extreme Greed";
}

function momentumLabel(
  score: number
): MarketMomentum["label"] {
  if (score <= -50) return "Strong Bearish";
  if (score <= -15) return "Bearish";
  if (score <= 15) return "Neutral";
  if (score <= 50) return "Bullish";
  return "Strong Bullish";
}

/**
 * Calculate synthetic sentiment from price changes when the API is unavailable.
 * Uses a simple heuristic: average of normalized price deltas mapped to 0-100.
 */
function syntheticSentiment(
  prices: Record<string, number>,
  prevPrices: Record<string, number>
): number {
  const symbols = ["BTC", "ETH", "SOL"];
  let totalPctChange = 0;
  let count = 0;

  for (const sym of symbols) {
    const curr = prices[sym];
    const prev = prevPrices[sym];
    if (curr && prev && prev > 0) {
      totalPctChange += ((curr - prev) / prev) * 100;
      count++;
    }
  }

  if (count === 0) return 50; // neutral default
  const avgChange = totalPctChange / count;
  // Map -5%..+5% to 0..100, clamped
  const mapped = 50 + avgChange * 10;
  return Math.max(0, Math.min(100, Math.round(mapped)));
}

/**
 * Calculate market momentum from price history.
 * Returns -100 to +100.
 */
function calculateMomentum(
  prices: Record<string, number>,
  prevPrices: Record<string, number>
): number {
  const symbols = ["BTC", "ETH", "SOL"];
  let totalPctChange = 0;
  let count = 0;

  for (const sym of symbols) {
    const curr = prices[sym];
    const prev = prevPrices[sym];
    if (curr && prev && prev > 0) {
      totalPctChange += ((curr - prev) / prev) * 100;
      count++;
    }
  }

  if (count === 0) return 0;
  const avgChange = totalPctChange / count;
  // Map -3%..+3% to -100..+100
  return Math.max(-100, Math.min(100, Math.round(avgChange * 33.3)));
}

/**
 * Calculate volatility from price variance.
 * Simple approach: magnitude of price swings.
 */
function calculateVolatility(
  prices: Record<string, number>,
  prevPrices: Record<string, number>
): number {
  const symbols = ["BTC", "ETH", "SOL"];
  let totalAbsChange = 0;
  let count = 0;

  for (const sym of symbols) {
    const curr = prices[sym];
    const prev = prevPrices[sym];
    if (curr && prev && prev > 0) {
      totalAbsChange += Math.abs((curr - prev) / prev) * 100;
      count++;
    }
  }

  if (count === 0) return 30; // default medium-low
  const avgAbsChange = totalAbsChange / count;
  // Map 0-5% absolute change to 0-100
  return Math.max(0, Math.min(100, Math.round(avgAbsChange * 20)));
}

function volatilityLabel(score: number): VolatilityLevel["label"] {
  if (score < 33) return "Low";
  if (score < 66) return "Medium";
  return "High";
}

const POLL_INTERVAL = 5 * 60 * 1000; // 5 minutes

export function useSentiment(
  prices: Record<string, number>
): SentimentResult {
  const [sentiment, setSentiment] = useState<SentimentData>({
    value: 50,
    classification: "Neutral",
    timestamp: new Date().toISOString(),
    loading: true,
    error: null,
  });

  const prevPricesRef = useRef<Record<string, number>>({ ...prices });
  const snapshotPricesRef = useRef<Record<string, number>>({ ...prices });
  const mountedRef = useRef(true);
  const apiAvailableRef = useRef(true);

  // Take a snapshot of prices every 60s for momentum/volatility calculations
  useEffect(() => {
    const id = setInterval(() => {
      snapshotPricesRef.current = { ...prevPricesRef.current };
      prevPricesRef.current = { ...prices };
    }, 60_000);

    return () => clearInterval(id);
  }, [prices]);

  // Keep prevPricesRef updated
  useEffect(() => {
    // Only update if we have real data
    const hasPrices = Object.keys(prices).length > 0;
    if (hasPrices) {
      prevPricesRef.current = { ...prices };
    }
  }, [prices]);

  const fetchSentiment = useCallback(async () => {
    if (!mountedRef.current) return;

    try {
      const res = await fetch("https://api.alternative.me/fng/?limit=1", {
        signal: AbortSignal.timeout(5000),
      });
      if (!res.ok) throw new Error(`API ${res.status}`);
      const json = await res.json();
      const entry = json?.data?.[0];

      if (!entry || !entry.value) throw new Error("Invalid response");

      const value = parseInt(entry.value, 10);
      if (isNaN(value)) throw new Error("Invalid value");

      if (mountedRef.current) {
        apiAvailableRef.current = true;
        setSentiment({
          value,
          classification: entry.value_classification || classify(value),
          timestamp: entry.timestamp
            ? new Date(parseInt(entry.timestamp, 10) * 1000).toISOString()
            : new Date().toISOString(),
          loading: false,
          error: null,
        });
      }
    } catch (err) {
      if (!mountedRef.current) return;
      apiAvailableRef.current = false;

      // Fallback: synthetic sentiment from prices
      const synth = syntheticSentiment(
        prevPricesRef.current,
        snapshotPricesRef.current
      );
      setSentiment({
        value: synth,
        classification: classify(synth),
        timestamp: new Date().toISOString(),
        loading: false,
        error: err instanceof Error ? err.message : "API unavailable",
      });
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    fetchSentiment();

    const id = setInterval(fetchSentiment, POLL_INTERVAL);
    return () => {
      mountedRef.current = false;
      clearInterval(id);
    };
  }, [fetchSentiment]);

  // Calculate derived metrics
  const momScore = calculateMomentum(prices, snapshotPricesRef.current);
  const volScore = calculateVolatility(prices, snapshotPricesRef.current);

  // BTC dominance trend (simulated based on BTC vs altcoin performance)
  const btcChange =
    prices.BTC && snapshotPricesRef.current.BTC
      ? ((prices.BTC - snapshotPricesRef.current.BTC) /
          snapshotPricesRef.current.BTC) *
        100
      : 0;
  const ethChange =
    prices.ETH && snapshotPricesRef.current.ETH
      ? ((prices.ETH - snapshotPricesRef.current.ETH) /
          snapshotPricesRef.current.ETH) *
        100
      : 0;
  const btcDominanceTrend: SentimentResult["btcDominanceTrend"] =
    btcChange - ethChange > 0.5
      ? "rising"
      : btcChange - ethChange < -0.5
        ? "falling"
        : "stable";

  return {
    sentiment,
    momentum: {
      score: momScore,
      label: momentumLabel(momScore),
    },
    volatility: {
      score: volScore,
      label: volatilityLabel(volScore),
    },
    btcDominanceTrend,
  };
}
