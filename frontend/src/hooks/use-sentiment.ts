// =============================================================================
// src/hooks/use-sentiment.ts — Multi-Market Sentiment
//
// Crypto: Fear & Greed from alternative.me + BTC dominance from CoinGecko.
// Stocks: CNN Fear & Greed Index + VIX-based volatility.
// Commodities: Sentiment computed from GLD price movement (14-day trend).
// Momentum & Volatility: Derived from priceHistory ring buffer per market.
// =============================================================================

"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type MarketTab = "crypto" | "stocks" | "commodities";

export interface SentimentData {
  value: number; // 0-100
  classification: string;
  timestamp: string;
  history: number[]; // last 7 values (oldest→newest)
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
  value: number | null;
  trend: "rising" | "falling" | "stable";
}

export interface MarketSentiment {
  sentiment: SentimentData;
  momentum: MarketMomentum;
  volatility: VolatilityLevel;
  /** Extra indicator label — BTC Dom. for crypto, VIX for stocks, Gold Trend for commodities */
  extraLabel: string;
  extraValue: string;
  extraColor: string;
  extraTrend: "rising" | "falling" | "stable";
}

export interface SentimentResult {
  activeTab: MarketTab;
  setActiveTab: (tab: MarketTab) => void;
  crypto: MarketSentiment;
  stocks: MarketSentiment;
  commodities: MarketSentiment;
  /** Pearson-like correlation between crypto and stocks momentum */
  correlation: { value: number; label: string } | null;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

export function classify(value: number): string {
  if (value <= 25) return "Extreme Fear";
  if (value <= 45) return "Fear";
  if (value <= 55) return "Neutral";
  if (value <= 75) return "Greed";
  return "Extreme Greed";
}

export function momentumLabel(score: number): MarketMomentum["label"] {
  if (score <= -50) return "Strong Bearish";
  if (score <= -15) return "Bearish";
  if (score <= 15) return "Neutral";
  if (score <= 50) return "Bullish";
  return "Strong Bullish";
}

export function volatilityLabel(score: number): VolatilityLevel["label"] {
  if (score < 33) return "Low";
  if (score < 66) return "Medium";
  return "High";
}

export function calculateMomentumFromHistory(
  priceHistory: Record<string, number[]>,
  symbols: string[]
): number {
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

export function calculateVolatilityFromHistory(
  priceHistory: Record<string, number[]>,
  symbols: string[]
): number {
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
  return Math.max(0, Math.min(100, Math.round(avgCV * 20000)));
}

/** Compute a simple sentiment score from price trend (0-100). */
function sentimentFromPriceTrend(
  priceHistory: Record<string, number[]>,
  symbols: string[]
): number {
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
  if (count === 0) return 50;
  const avg = totalPct / count;
  // Map -1%..+1% to 0..100
  return Math.max(0, Math.min(100, Math.round(50 + avg * 50)));
}

// ---------------------------------------------------------------------------
// Market asset groups
// ---------------------------------------------------------------------------

const CRYPTO_SYMBOLS = ["BTC", "ETH", "SOL"];
const STOCK_SYMBOLS = ["SPY", "AAPL", "NVDA", "TSLA"];
const COMMODITY_SYMBOLS = ["GLD"];

const POLL_INTERVAL = 5 * 60 * 1000; // 5 minutes

// ---------------------------------------------------------------------------
// Default sentiment data
// ---------------------------------------------------------------------------

function defaultSentiment(loading = true): SentimentData {
  return {
    value: 50,
    classification: "Neutral",
    timestamp: new Date().toISOString(),
    history: [],
    loading,
    error: null,
  };
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useSentiment(
  prices: Record<string, number>,
  priceHistory?: Record<string, number[]>
): SentimentResult {
  const [activeTab, setActiveTab] = useState<MarketTab>("crypto");

  // --- Crypto F&G ---
  const [cryptoSentiment, setCryptoSentiment] = useState<SentimentData>(
    defaultSentiment()
  );
  // --- Stocks F&G ---
  const [stocksSentiment, setStocksSentiment] = useState<SentimentData>(
    defaultSentiment()
  );
  // --- BTC Dominance ---
  const [btcDominance, setBtcDominance] = useState<BtcDominance>({
    value: null,
    trend: "stable",
  });
  // --- VIX proxy ---
  const [vixValue, setVixValue] = useState<number | null>(null);

  const mountedRef = useRef(true);
  const prevDominanceRef = useRef<number | null>(null);

  // =========================================================================
  // Fetch: Crypto Fear & Greed (alternative.me)
  // =========================================================================
  const fetchCryptoFG = useCallback(async () => {
    if (!mountedRef.current) return;
    try {
      const res = await fetch("https://api.alternative.me/fng/?limit=7", {
        signal: AbortSignal.timeout(5000),
      });
      if (!res.ok) throw new Error(`API ${res.status}`);
      const json = await res.json();
      const entries = json?.data;
      if (!entries || !Array.isArray(entries) || entries.length === 0)
        throw new Error("Invalid response");

      const latest = entries[0];
      const value = parseInt(latest.value, 10);
      if (isNaN(value)) throw new Error("Invalid value");

      const history = entries
        .map((e: { value: string }) => parseInt(e.value, 10))
        .filter((v: number) => !isNaN(v))
        .reverse();

      if (mountedRef.current) {
        setCryptoSentiment({
          value,
          classification: latest.value_classification || classify(value),
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
      const synth = sentimentFromPriceTrend(
        priceHistory ?? {},
        CRYPTO_SYMBOLS
      );
      setCryptoSentiment((prev) => ({
        ...prev,
        value: synth,
        classification: classify(synth),
        timestamp: new Date().toISOString(),
        loading: false,
        error: err instanceof Error ? err.message : "API unavailable",
      }));
    }
  }, [priceHistory]);

  // =========================================================================
  // Fetch: CNN Stock Market Fear & Greed
  // =========================================================================
  const fetchStocksFG = useCallback(async () => {
    if (!mountedRef.current) return;
    try {
      const res = await fetch(
        "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
        { signal: AbortSignal.timeout(5000) }
      );
      if (!res.ok) throw new Error(`CNN ${res.status}`);
      const json = await res.json();

      // CNN response shape: { fear_and_greed: { score, rating, ... }, fear_and_greed_historical: { data: [...] } }
      const fng = json?.fear_and_greed;
      if (!fng || typeof fng.score !== "number") throw new Error("Invalid CNN data");

      const value = Math.round(fng.score);
      const rating: string = fng.rating ?? classify(value);

      // Historical: last 7 data points
      const histData = json?.fear_and_greed_historical?.data ?? [];
      const history = histData
        .slice(-7)
        .map((d: { x: number; y: number }) => Math.round(d.y))
        .filter((v: number) => !isNaN(v));

      if (mountedRef.current) {
        setStocksSentiment({
          value,
          classification: rating.charAt(0).toUpperCase() + rating.slice(1).toLowerCase(),
          timestamp: new Date().toISOString(),
          history,
          loading: false,
          error: null,
        });
      }
    } catch (err) {
      if (!mountedRef.current) return;
      // Fallback: compute from stock price movement
      const synth = sentimentFromPriceTrend(
        priceHistory ?? {},
        STOCK_SYMBOLS
      );
      setStocksSentiment((prev) => ({
        ...prev,
        value: synth,
        classification: classify(synth),
        timestamp: new Date().toISOString(),
        loading: false,
        error: err instanceof Error ? err.message : "CNN unavailable",
      }));
    }
  }, [priceHistory]);

  // =========================================================================
  // Fetch: BTC Dominance (CoinGecko) + VIX proxy
  // =========================================================================
  const fetchExtras = useCallback(async () => {
    if (!mountedRef.current) return;

    // BTC Dominance
    try {
      const res = await fetch("https://api.coingecko.com/api/v3/global", {
        signal: AbortSignal.timeout(5000),
      });
      if (!res.ok) throw new Error(`CoinGecko ${res.status}`);
      const json = await res.json();
      const dom = json?.data?.market_cap_percentage?.btc;
      if (typeof dom === "number" && mountedRef.current) {
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
      // keep previous
    }

    // VIX proxy: derive from stock volatility (no free VIX API without key)
    // We use stock price volatility as a proxy scaled to VIX-like range (12-40)
    if (priceHistory) {
      const volScore = calculateVolatilityFromHistory(
        priceHistory,
        STOCK_SYMBOLS
      );
      // Map 0-100 volatility score to VIX-like 12-40 range
      const vix = Math.round(12 + (volScore / 100) * 28);
      if (mountedRef.current) setVixValue(vix);
    }
  }, [priceHistory]);

  // =========================================================================
  // Polling
  // =========================================================================
  useEffect(() => {
    mountedRef.current = true;
    fetchCryptoFG();
    fetchStocksFG();
    fetchExtras();

    const id = setInterval(() => {
      fetchCryptoFG();
      fetchStocksFG();
      fetchExtras();
    }, POLL_INTERVAL);

    return () => {
      mountedRef.current = false;
      clearInterval(id);
    };
  }, [fetchCryptoFG, fetchStocksFG, fetchExtras]);

  // =========================================================================
  // Derived: per-market momentum + volatility
  // =========================================================================
  const cryptoMom = useMemo(() => {
    const score = priceHistory
      ? calculateMomentumFromHistory(priceHistory, CRYPTO_SYMBOLS)
      : 0;
    return { score, label: momentumLabel(score) };
  }, [priceHistory]);

  const cryptoVol = useMemo(() => {
    const score = priceHistory
      ? calculateVolatilityFromHistory(priceHistory, CRYPTO_SYMBOLS)
      : 30;
    return { score, label: volatilityLabel(score) };
  }, [priceHistory]);

  const stocksMom = useMemo(() => {
    const score = priceHistory
      ? calculateMomentumFromHistory(priceHistory, STOCK_SYMBOLS)
      : 0;
    return { score, label: momentumLabel(score) };
  }, [priceHistory]);

  const stocksVol = useMemo(() => {
    const score = priceHistory
      ? calculateVolatilityFromHistory(priceHistory, STOCK_SYMBOLS)
      : 30;
    return { score, label: volatilityLabel(score) };
  }, [priceHistory]);

  const commoditiesMom = useMemo(() => {
    const score = priceHistory
      ? calculateMomentumFromHistory(priceHistory, COMMODITY_SYMBOLS)
      : 0;
    return { score, label: momentumLabel(score) };
  }, [priceHistory]);

  const commoditiesVol = useMemo(() => {
    const score = priceHistory
      ? calculateVolatilityFromHistory(priceHistory, COMMODITY_SYMBOLS)
      : 30;
    return { score, label: volatilityLabel(score) };
  }, [priceHistory]);

  // =========================================================================
  // Derived: commodities sentiment (no API — from price trend)
  // =========================================================================
  const commoditiesSentiment = useMemo<SentimentData>(() => {
    if (!priceHistory || !priceHistory.GLD || priceHistory.GLD.length < 2) {
      return defaultSentiment(false);
    }
    const synth = sentimentFromPriceTrend(priceHistory, COMMODITY_SYMBOLS);
    return {
      value: synth,
      classification: classify(synth),
      timestamp: new Date().toISOString(),
      history: priceHistory.GLD.map((p) => {
        // Normalize GLD prices to 0-100 range for sparkline consistency
        const base = priceHistory.GLD[0];
        const pct = base > 0 ? ((p - base) / base) * 100 : 0;
        return Math.max(0, Math.min(100, Math.round(50 + pct * 50)));
      }),
      loading: false,
      error: "Computed from price",
    };
  }, [priceHistory]);

  // =========================================================================
  // Correlation: crypto vs stocks momentum alignment
  // =========================================================================
  const correlation = useMemo(() => {
    if (cryptoMom.score === 0 && stocksMom.score === 0) return null;
    // Simple: same sign & magnitude → high correlation
    const sameDirection =
      (cryptoMom.score > 0 && stocksMom.score > 0) ||
      (cryptoMom.score < 0 && stocksMom.score < 0);
    const avgMag =
      (Math.abs(cryptoMom.score) + Math.abs(stocksMom.score)) / 2;

    if (sameDirection && avgMag > 30) {
      return { value: avgMag, label: "Crypto & Stocks correlating" };
    }
    if (!sameDirection && avgMag > 30) {
      return { value: -avgMag, label: "Crypto & Stocks diverging" };
    }
    return null;
  }, [cryptoMom.score, stocksMom.score]);

  // =========================================================================
  // Build per-market results
  // =========================================================================

  // Extra indicator helpers
  const domLabel = btcDominance.value !== null ? `${btcDominance.value}%` : "—";
  const domColor =
    btcDominance.trend === "rising"
      ? "text-orange-400"
      : btcDominance.trend === "falling"
        ? "text-blue-400"
        : "text-zinc-400";

  const vixColor =
    vixValue !== null
      ? vixValue > 25
        ? "text-red-400"
        : vixValue > 18
          ? "text-yellow-400"
          : "text-green-400"
      : "text-zinc-400";

  const gldTrend: "rising" | "falling" | "stable" =
    commoditiesMom.score > 15
      ? "rising"
      : commoditiesMom.score < -15
        ? "falling"
        : "stable";

  const crypto: MarketSentiment = {
    sentiment: cryptoSentiment,
    momentum: cryptoMom,
    volatility: cryptoVol,
    extraLabel: "BTC Dom.",
    extraValue: domLabel,
    extraColor: domColor,
    extraTrend: btcDominance.trend,
  };

  const stocks: MarketSentiment = {
    sentiment: stocksSentiment,
    momentum: stocksMom,
    volatility: stocksVol,
    extraLabel: "VIX",
    extraValue: vixValue !== null ? `${vixValue}` : "—",
    extraColor: vixColor,
    extraTrend:
      vixValue !== null
        ? vixValue > 25
          ? "rising"
          : vixValue < 18
            ? "falling"
            : "stable"
        : "stable",
  };

  const commodities: MarketSentiment = {
    sentiment: commoditiesSentiment,
    momentum: commoditiesMom,
    volatility: commoditiesVol,
    extraLabel: "Gold Trend",
    extraValue:
      gldTrend === "rising"
        ? "Bullish"
        : gldTrend === "falling"
          ? "Bearish"
          : "Neutral",
    extraColor:
      gldTrend === "rising"
        ? "text-yellow-400"
        : gldTrend === "falling"
          ? "text-red-400"
          : "text-zinc-400",
    extraTrend: gldTrend,
  };

  return {
    activeTab,
    setActiveTab,
    crypto,
    stocks,
    commodities,
    correlation,
  };
}
