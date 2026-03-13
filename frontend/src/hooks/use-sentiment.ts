// =============================================================================
// src/hooks/use-sentiment.ts — Multi-Market Sentiment (v3)
//
// Crypto: alternative.me F&G + intraday BTC momentum adjustment (±10).
// Stocks: CNN F&G via /api/sentiment proxy (no CORS) + VIX proxy.
// Commodities: Composite F&G from momentum, volatility, price-vs-MA.
// Momentum & Volatility: From priceHistory ring buffer (60 snapshots, 3min).
// BTC Dominance: CoinGecko via /api/sentiment proxy.
//
// v3 fixes: callback dep leak, maFactor math, consolidated memos, error flag.
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
  correlation: { value: number; label: string } | null;
}

// ---------------------------------------------------------------------------
// Helpers (exported for tests)
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
  // 3min buffer: ±0.3% typical → map to ±100
  return Math.max(-100, Math.min(100, Math.round(avg * 333)));
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
  // 3min buffer: CV ~0.001 for moderate vol → map to 0-100
  return Math.max(0, Math.min(100, Math.round(avgCV * 50000)));
}

/**
 * Composite commodity F&G from multiple factors (0-100):
 * 40% momentum trend, 30% inverse volatility, 30% price vs simple MA.
 */
export function compositeCommodityFG(
  priceHistory: Record<string, number[]>,
  symbols: string[]
): number {
  // Factor 1: momentum (map ±100 → 0-100)
  const mom = calculateMomentumFromHistory(priceHistory, symbols);
  const momFactor = Math.max(0, Math.min(100, 50 + mom * 0.5));

  // Factor 2: inverse volatility (low vol = greed, high vol = fear)
  const vol = calculateVolatilityFromHistory(priceHistory, symbols);
  const volFactor = 100 - vol;

  // Factor 3: price vs simple moving average (per-symbol, then average)
  let maTotal = 0;
  let maCount = 0;
  for (const sym of symbols) {
    const hist = priceHistory[sym];
    if (!hist || hist.length < 5) continue;
    const ma = hist.reduce((s, v) => s + v, 0) / hist.length;
    const latest = hist[hist.length - 1];
    if (ma > 0) {
      const pctAbove = ((latest - ma) / ma) * 100;
      // Map ±1% above/below MA to 0-100
      maTotal += Math.max(0, Math.min(100, 50 + pctAbove * 50));
      maCount++;
    }
  }
  const maFactor = maCount > 0 ? maTotal / maCount : 50;

  // Weighted composite
  const composite = Math.round(momFactor * 0.4 + volFactor * 0.3 + maFactor * 0.3);
  return Math.max(0, Math.min(100, composite));
}

// ---------------------------------------------------------------------------
// Market asset groups
// ---------------------------------------------------------------------------

const CRYPTO_SYMBOLS = ["BTC", "ETH", "SOL"];
const STOCK_SYMBOLS = ["SPY", "AAPL", "NVDA", "TSLA"];
const COMMODITY_SYMBOLS = ["GLD"];

const POLL_INTERVAL = 5 * 60 * 1000; // 5 minutes

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

  const [cryptoSentiment, setCryptoSentiment] = useState<SentimentData>(
    defaultSentiment()
  );
  const [stocksSentiment, setStocksSentiment] = useState<SentimentData>(
    defaultSentiment()
  );
  const [btcDominance, setBtcDominance] = useState<BtcDominance>({
    value: null,
    trend: "stable",
  });

  const mountedRef = useRef(true);
  const prevDominanceRef = useRef<number | null>(null);

  // Use refs for priceHistory to avoid callback dependency churn.
  // This prevents the polling interval from resetting every 3s.
  const priceHistoryRef = useRef(priceHistory);
  priceHistoryRef.current = priceHistory;

  // =========================================================================
  // Fetch: Crypto Fear & Greed (alternative.me) + intraday adjustment
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
      let value = parseInt(latest.value, 10);
      if (isNaN(value)) throw new Error("Invalid value");

      // Intraday adjustment: BTC momentum ±10 points
      const ph = priceHistoryRef.current;
      if (ph?.BTC && ph.BTC.length >= 5) {
        const btcHist = ph.BTC;
        const first = btcHist[0];
        const last = btcHist[btcHist.length - 1];
        if (first > 0) {
          const pctChange = ((last - first) / first) * 100;
          const adjustment = Math.max(-10, Math.min(10, Math.round(pctChange * 33.3)));
          value = Math.max(0, Math.min(100, value + adjustment));
        }
      }

      const history = entries
        .map((e: { value: string }) => parseInt(e.value, 10))
        .filter((v: number) => !isNaN(v))
        .reverse();

      if (mountedRef.current) {
        setCryptoSentiment({
          value,
          classification: classify(value),
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
      // Fallback: derive from BTC momentum
      let synth = 50;
      const ph = priceHistoryRef.current;
      if (ph?.BTC && ph.BTC.length >= 2) {
        const btcH = ph.BTC;
        const pct = ((btcH[btcH.length - 1] - btcH[0]) / btcH[0]) * 100;
        synth = Math.max(0, Math.min(100, Math.round(50 + pct * 100)));
      }
      setCryptoSentiment((prev) => ({
        ...prev,
        value: synth,
        classification: classify(synth),
        timestamp: new Date().toISOString(),
        loading: false,
        error: err instanceof Error ? err.message : "API unavailable",
      }));
    }
  }, []); // No priceHistory dep — uses ref

  // =========================================================================
  // Fetch: CNN Stocks F&G + CoinGecko via /api/sentiment proxy
  // =========================================================================
  const fetchProxy = useCallback(async () => {
    if (!mountedRef.current) return;
    try {
      const res = await fetch("/api/sentiment", {
        signal: AbortSignal.timeout(10000),
      });
      if (!res.ok) throw new Error(`Proxy ${res.status}`);
      const json = await res.json();

      // --- CNN Stocks F&G ---
      if (json.cnn) {
        const { score, rating, history } = json.cnn;
        if (mountedRef.current) {
          setStocksSentiment({
            value: score,
            classification:
              rating
                ? rating.charAt(0).toUpperCase() + rating.slice(1).toLowerCase()
                : classify(score),
            timestamp: new Date().toISOString(),
            history: Array.isArray(history) ? history : [],
            loading: false,
            error: null,
          });
        }
      } else {
        throw new Error(json.cnnError || "CNN data unavailable");
      }

      // --- CoinGecko: BTC Dominance ---
      if (json.gecko && mountedRef.current) {
        const rounded = json.gecko.btcDominance;
        if (typeof rounded === "number") {
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
      }
    } catch (err) {
      if (!mountedRef.current) return;
      // Stocks fallback: from price history
      let synth = 50;
      const ph = priceHistoryRef.current;
      if (ph) {
        const mom = calculateMomentumFromHistory(ph, STOCK_SYMBOLS);
        synth = Math.max(0, Math.min(100, 50 + Math.round(mom * 0.5)));
      }
      setStocksSentiment((prev) => ({
        ...prev,
        value: synth,
        classification: classify(synth),
        timestamp: new Date().toISOString(),
        loading: false,
        error: err instanceof Error ? err.message : "Proxy unavailable",
      }));
    }
  }, []); // No priceHistory dep — uses ref

  // =========================================================================
  // Polling — stable interval (callbacks have no deps that churn)
  // =========================================================================
  useEffect(() => {
    mountedRef.current = true;
    fetchCryptoFG();
    fetchProxy();

    const id = setInterval(() => {
      fetchCryptoFG();
      fetchProxy();
    }, POLL_INTERVAL);

    return () => {
      mountedRef.current = false;
      clearInterval(id);
    };
  }, [fetchCryptoFG, fetchProxy]);

  // =========================================================================
  // Derived: all per-market metrics in one memo (avoids 7 separate memos)
  // =========================================================================
  const derived = useMemo(() => {
    const ph = priceHistory ?? {};

    const mkMom = (symbols: string[]) => {
      const score = calculateMomentumFromHistory(ph, symbols);
      return { score, label: momentumLabel(score) };
    };
    const mkVol = (symbols: string[]) => {
      const score = calculateVolatilityFromHistory(ph, symbols);
      return { score, label: volatilityLabel(score) };
    };

    const cryptoMom = mkMom(CRYPTO_SYMBOLS);
    const cryptoVol = mkVol(CRYPTO_SYMBOLS);
    const stocksMom = mkMom(STOCK_SYMBOLS);
    const stocksVol = mkVol(STOCK_SYMBOLS);
    const commoditiesMom = mkMom(COMMODITY_SYMBOLS);
    const commoditiesVol = mkVol(COMMODITY_SYMBOLS);

    // VIX proxy from stock volatility
    const vixValue = Math.round(12 + (stocksVol.score / 100) * 28);

    // Commodities composite F&G
    let commoditiesFG: SentimentData;
    if (ph.GLD && ph.GLD.length >= 5) {
      const composite = compositeCommodityFG(ph, COMMODITY_SYMBOLS);
      const gld = ph.GLD;
      const step = Math.max(1, Math.floor(gld.length / 7));
      const sparkHistory: number[] = [];
      for (let i = 0; i < gld.length; i += step) {
        const base = gld[0];
        const pct = base > 0 ? ((gld[i] - base) / base) * 100 : 0;
        sparkHistory.push(Math.max(0, Math.min(100, Math.round(50 + pct * 100))));
      }
      commoditiesFG = {
        value: composite,
        classification: classify(composite),
        timestamp: new Date().toISOString(),
        history: sparkHistory,
        loading: false,
        error: null, // Not an error — computed is normal for commodities
      };
    } else {
      commoditiesFG = defaultSentiment(false);
    }

    // Correlation
    let correlation: SentimentResult["correlation"] = null;
    if (cryptoMom.score !== 0 || stocksMom.score !== 0) {
      const sameDirection =
        (cryptoMom.score > 0 && stocksMom.score > 0) ||
        (cryptoMom.score < 0 && stocksMom.score < 0);
      const avgMag =
        (Math.abs(cryptoMom.score) + Math.abs(stocksMom.score)) / 2;
      if (sameDirection && avgMag > 30) {
        correlation = { value: avgMag, label: "Crypto & Stocks correlating" };
      } else if (!sameDirection && avgMag > 30) {
        correlation = { value: -avgMag, label: "Crypto & Stocks diverging" };
      }
    }

    return {
      cryptoMom,
      cryptoVol,
      stocksMom,
      stocksVol,
      commoditiesMom,
      commoditiesVol,
      vixValue,
      commoditiesFG,
      correlation,
    };
  }, [priceHistory]);

  // =========================================================================
  // Build per-market results
  // =========================================================================
  const {
    cryptoMom, cryptoVol, stocksMom, stocksVol,
    commoditiesMom, commoditiesVol, vixValue,
    commoditiesFG, correlation,
  } = derived;

  const domLabel = btcDominance.value !== null ? `${btcDominance.value}%` : "—";
  const domColor =
    btcDominance.trend === "rising"
      ? "text-orange-400"
      : btcDominance.trend === "falling"
        ? "text-blue-400"
        : "text-zinc-400";

  const vixColor =
    vixValue > 25
      ? "text-red-400"
      : vixValue > 18
        ? "text-yellow-400"
        : "text-green-400";

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
    extraValue: `${vixValue}`,
    extraColor: vixColor,
    extraTrend:
      vixValue > 25 ? "rising" : vixValue < 18 ? "falling" : "stable",
  };

  const commodities: MarketSentiment = {
    sentiment: commoditiesFG,
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
