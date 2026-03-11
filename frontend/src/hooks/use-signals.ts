"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { batchPredict, type AssetPrediction } from "@/lib/api";
import type { Signal } from "@/lib/types";
import { DEFAULT_ASSETS } from "@/lib/constants";

function predictionToSignal(
  ap: AssetPrediction,
  basePrice: number
): Signal | null {
  if (!ap.prediction) return null;
  const p = ap.prediction;
  const direction: "LONG" | "SHORT" = p.mu >= 0 ? "LONG" : "SHORT";
  const sigma = Math.max(p.sigma, 0.001);

  return {
    id: `${ap.asset}-${Date.now()}`,
    asset: ap.asset,
    direction,
    entry: basePrice,
    stopLoss:
      direction === "LONG"
        ? basePrice * (1 - sigma * 2)
        : basePrice * (1 + sigma * 2),
    takeProfit:
      direction === "LONG"
        ? basePrice * (1 + sigma * 3)
        : basePrice * (1 - sigma * 3),
    confidence: p.confidence,
    qualityScore: p.quality_score,
    regime: p.regime,
    isOod: p.is_ood,
    timestamp: new Date(),
  };
}

// Generate deterministic synthetic features per asset as Dict[str, float]
function featuresForAsset(symbol: string): Record<string, number> {
  let hash = 0;
  for (let i = 0; i < symbol.length; i++) {
    hash = (hash * 31 + symbol.charCodeAt(i)) & 0xffff;
  }
  const keys = [
    "momentum", "volatility", "trend", "volume", "rsi",
    "macd", "bb_width", "atr", "obv", "vwap",
  ];
  const features: Record<string, number> = {};
  keys.forEach((key, i) => {
    features[key] = parseFloat((Math.sin(hash + i * 1.7) * 0.5).toFixed(4));
  });
  return features;
}

export function useSignals(
  regime: string = "RISK_ON",
  intervalMs: number = 10000
) {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  const refresh = useCallback(async () => {
    try {
      const assets = DEFAULT_ASSETS.map((a) => ({
        symbol: a.symbol,
        features: featuresForAsset(a.symbol),
      }));
      const results = await batchPredict(assets, regime);
      if (!mountedRef.current) return;

      const newSignals = results
        .map((ap) => {
          const asset = DEFAULT_ASSETS.find((a) => a.symbol === ap.asset);
          if (!asset) return null;
          return predictionToSignal(ap, asset.price);
        })
        .filter((s): s is Signal => s !== null);

      setSignals(newSignals);
      setError(null);
    } catch (err) {
      if (!mountedRef.current) return;
      setError(err instanceof Error ? err.message : "Signal fetch failed");
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, [regime]);

  useEffect(() => {
    mountedRef.current = true;
    refresh();
    const id = setInterval(refresh, intervalMs);
    return () => {
      mountedRef.current = false;
      clearInterval(id);
    };
  }, [refresh, intervalMs]);

  return { signals, loading, error, refresh };
}
