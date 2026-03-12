// =============================================================================
// src/components/chart/asset-chart.tsx — Multi-Asset Candlestick Chart
//
// Crypto (BTC, ETH, SOL): Real Binance OHLC klines.
// Other assets: Synthetic candlestick data.
// Uses TradingView Lightweight Charts with JARVIS signal overlay markers.
// =============================================================================

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  createChart,
  type IChartApi,
  ColorType,
  type CandlestickData as LWCandlestickData,
  type Time,
} from "lightweight-charts";
import type { RegimeState } from "@/lib/types";
import { REGIME_COLORS } from "@/lib/types";
import { useBinanceKlines, type Kline } from "@/hooks/use-binance-klines";

// ---------------------------------------------------------------------------
// Synthetic data generation — for non-crypto assets
// ---------------------------------------------------------------------------

interface CandlePoint {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
}

interface SignalMarker {
  time: string;
  position: "aboveBar" | "belowBar";
  color: string;
  shape: "arrowUp" | "arrowDown" | "circle";
  text: string;
}

function hashSymbol(symbol: string): number {
  let h = 0;
  for (let i = 0; i < symbol.length; i++) {
    h = (h * 31 + symbol.charCodeAt(i)) & 0xffff;
  }
  return h;
}

function generateAssetData(
  symbol: string,
  basePrice: number,
  days: number
): CandlePoint[] {
  const data: CandlePoint[] = [];
  const seed = hashSymbol(symbol);
  const now = new Date();

  for (let i = days; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().split("T")[0];

    const t = (days - i) / days;
    const trend = Math.sin(t * Math.PI * 2 + seed * 0.1) * basePrice * 0.05;
    const noise =
      Math.sin((days - i) * 0.7 + seed) * basePrice * 0.012 +
      Math.cos((days - i) * 1.3 + seed * 0.5) * basePrice * 0.006;
    const price = basePrice + trend + noise;

    const volScale = basePrice * 0.008;
    const volatility =
      volScale + Math.abs(Math.sin((days - i) * 0.3 + seed)) * volScale * 3;
    const open =
      price + Math.sin((days - i) * 2.1 + seed) * volatility * 0.3;
    const close =
      price + Math.cos((days - i) * 1.7 + seed) * volatility * 0.3;
    const high =
      Math.max(open, close) +
      Math.abs(Math.sin((days - i) * 3.1 + seed)) * volatility * 0.5;
    const low =
      Math.min(open, close) -
      Math.abs(Math.cos((days - i) * 2.7 + seed)) * volatility * 0.5;

    data.push({
      time: dateStr,
      open: Math.round(open * 100) / 100,
      high: Math.round(high * 100) / 100,
      low: Math.round(low * 100) / 100,
      close: Math.round(close * 100) / 100,
    });
  }

  return data;
}

function klinesToCandles(klines: Kline[]): CandlePoint[] {
  return klines.map((k) => ({
    time: k.time,
    open: k.open,
    high: k.high,
    low: k.low,
    close: k.close,
  }));
}

function generateSignalMarkers(
  data: CandlePoint[],
  regime: RegimeState,
  seed: number
): SignalMarker[] {
  const markers: SignalMarker[] = [];
  const step = 5 + (seed % 4);

  for (let i = 5; i < data.length; i += step) {
    const candle = data[i];
    const momentum = candle.close - data[i - 5].close;
    const isBullish = momentum > 0;

    markers.push({
      time: candle.time,
      position: isBullish ? "belowBar" : "aboveBar",
      color: isBullish ? "#22c55e" : "#ef4444",
      shape: isBullish ? "arrowUp" : "arrowDown",
      text: isBullish ? "LONG" : "SHORT",
    });
  }

  if (regime === "CRISIS" && data.length > 0) {
    const last = data[data.length - 1];
    markers.push({
      time: last.time,
      position: "aboveBar",
      color: REGIME_COLORS.CRISIS,
      shape: "circle",
      text: "CRISIS",
    });
  }

  return markers;
}

function generateVolumeData(data: CandlePoint[], seed: number, klines?: Kline[]) {
  return data.map((candle, i) => ({
    time: candle.time,
    value: klines?.[i]?.volume ?? 1000000 + Math.abs(Math.sin(i * 0.5 + seed)) * 5000000,
    color:
      candle.close >= candle.open
        ? "rgba(34, 197, 94, 0.3)"
        : "rgba(239, 68, 68, 0.3)",
  }));
}

// ---------------------------------------------------------------------------
// Chart Component
// ---------------------------------------------------------------------------

interface AssetChartProps {
  symbol: string;
  name: string;
  basePrice: number;
  livePrice?: number;
  regime?: RegimeState;
  height?: number;
  interval?: string;
}

export function AssetChart({
  symbol,
  name,
  basePrice,
  livePrice,
  regime = "RISK_ON",
  height = 400,
  interval = "1d",
}: AssetChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [lastPrice, setLastPrice] = useState<number>(0);
  const [priceChange, setPriceChange] = useState<number>(0);

  const seed = hashSymbol(symbol);
  const { klines, isCrypto } = useBinanceKlines(symbol, interval, 90);

  const initChart = useCallback(() => {
    if (!containerRef.current) return;

    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#9ca3af",
        fontSize: 12,
      },
      grid: {
        vertLines: { color: "rgba(255, 255, 255, 0.04)" },
        horzLines: { color: "rgba(255, 255, 255, 0.04)" },
      },
      width: containerRef.current.clientWidth,
      height,
      crosshair: {
        vertLine: { color: "rgba(255, 255, 255, 0.1)" },
        horzLine: { color: "rgba(255, 255, 255, 0.1)" },
      },
      rightPriceScale: {
        borderColor: "rgba(255, 255, 255, 0.1)",
      },
      timeScale: {
        borderColor: "rgba(255, 255, 255, 0.1)",
        timeVisible: ["1m", "5m", "15m", "1h", "4h"].includes(interval),
      },
    });

    chartRef.current = chart;

    const candleSeries = chart.addCandlestickSeries({
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

    // Use real klines for crypto, synthetic for others
    const assetData =
      isCrypto && klines.length > 0
        ? klinesToCandles(klines)
        : generateAssetData(symbol, basePrice, 90);

    candleSeries.setData(assetData as unknown as LWCandlestickData<Time>[]);

    const markers = generateSignalMarkers(assetData, regime, seed);
    candleSeries.setMarkers(
      markers.map((m) => ({ ...m, time: m.time as Time }))
    );

    const volumeSeries = chart.addHistogramSeries({
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });

    chart.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });

    const volumeData = generateVolumeData(
      assetData,
      seed,
      isCrypto && klines.length > 0 ? klines : undefined
    );
    volumeSeries.setData(
      volumeData as unknown as { time: Time; value: number; color: string }[]
    );

    const last = assetData[assetData.length - 1];
    const prev = assetData.length > 1 ? assetData[assetData.length - 2] : last;
    setLastPrice(livePrice ?? last.close);
    setPriceChange(((last.close - prev.close) / prev.close) * 100);

    chart.timeScale().fitContent();
  }, [symbol, basePrice, height, regime, seed, livePrice, klines, isCrypto, interval]);

  useEffect(() => {
    initChart();

    const handleResize = () => {
      if (chartRef.current && containerRef.current) {
        chartRef.current.applyOptions({
          width: containerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [initChart]);

  const displayPrice = livePrice ?? lastPrice;
  const isPositive = priceChange >= 0;

  return (
    <div className="w-full">
      {/* Price Header */}
      <div className="flex items-baseline gap-4 mb-4">
        <h2 className="text-2xl font-bold text-white">
          {symbol}/USD
        </h2>
        <span className="text-xs text-muted-foreground">{name}</span>
        {isCrypto && klines.length > 0 && (
          <span className="text-[10px] text-green-400 bg-green-500/10 px-1.5 py-0.5 rounded">
            LIVE DATA
          </span>
        )}
        <span className="text-3xl font-mono font-bold text-white">
          $
          {displayPrice.toLocaleString("en-US", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })}
        </span>
        <span
          className={`text-sm font-mono font-medium ${
            isPositive ? "text-green-400" : "text-red-400"
          }`}
        >
          {isPositive ? "+" : ""}
          {priceChange.toFixed(2)}%
        </span>
      </div>

      {/* Chart */}
      <div ref={containerRef} className="w-full rounded-lg overflow-hidden" />

      {/* Legend */}
      <div className="flex gap-6 mt-3 text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-green-500" />
          LONG Signal
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-red-500" />
          SHORT Signal
        </span>
        <span className="flex items-center gap-1.5">
          <span
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: REGIME_COLORS[regime] }}
          />
          Regime: {regime.replace("_", " ")}
        </span>
        {!isCrypto && (
          <span className="text-yellow-400">Synthetic Data</span>
        )}
      </div>
    </div>
  );
}
