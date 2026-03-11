// =============================================================================
// src/components/chart/btc-chart.tsx — BTC/USD Candlestick Chart
//
// Uses TradingView Lightweight Charts for rendering.
// Includes JARVIS signal overlay as colored markers.
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

// ---------------------------------------------------------------------------
// Generate synthetic BTC/USD data for demo
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

function generateBTCData(days: number): CandlePoint[] {
  const data: CandlePoint[] = [];
  let price = 65000;
  const now = new Date();

  for (let i = days; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().split("T")[0];

    // Deterministic "random" walk using sine waves
    const t = (days - i) / days;
    const trend = Math.sin(t * Math.PI * 2) * 3000;
    const noise =
      Math.sin((days - i) * 0.7) * 800 +
      Math.cos((days - i) * 1.3) * 400;
    price = 65000 + trend + noise;

    const volatility = 500 + Math.abs(Math.sin((days - i) * 0.3)) * 1500;
    const open = price + Math.sin((days - i) * 2.1) * volatility * 0.3;
    const close = price + Math.cos((days - i) * 1.7) * volatility * 0.3;
    const high = Math.max(open, close) + Math.abs(Math.sin((days - i) * 3.1)) * volatility * 0.5;
    const low = Math.min(open, close) - Math.abs(Math.cos((days - i) * 2.7)) * volatility * 0.5;

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

function generateSignalMarkers(
  data: CandlePoint[],
  regime: RegimeState
): SignalMarker[] {
  const markers: SignalMarker[] = [];

  for (let i = 5; i < data.length; i += 7) {
    const candle = data[i];
    // Simple momentum signal: compare with 5-candle lookback
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

  // Add regime change markers
  if (regime === "CRISIS") {
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

// ---------------------------------------------------------------------------
// Volume data (synthetic)
// ---------------------------------------------------------------------------

function generateVolumeData(data: CandlePoint[]) {
  return data.map((candle, i) => ({
    time: candle.time,
    value: 1000000 + Math.abs(Math.sin(i * 0.5)) * 5000000,
    color:
      candle.close >= candle.open
        ? "rgba(34, 197, 94, 0.3)"
        : "rgba(239, 68, 68, 0.3)",
  }));
}

// ---------------------------------------------------------------------------
// Chart Component
// ---------------------------------------------------------------------------

interface BTCChartProps {
  regime?: RegimeState;
  height?: number;
}

export function BTCChart({ regime = "RISK_ON", height = 500 }: BTCChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [lastPrice, setLastPrice] = useState<number>(0);
  const [priceChange, setPriceChange] = useState<number>(0);

  const initChart = useCallback(() => {
    if (!containerRef.current) return;

    // Clean up existing chart
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
        timeVisible: false,
      },
    });

    chartRef.current = chart;

    // Candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

    const btcData = generateBTCData(90);
    candleSeries.setData(
      btcData as unknown as LWCandlestickData<Time>[]
    );

    // Signal markers
    const markers = generateSignalMarkers(btcData, regime);
    candleSeries.setMarkers(
      markers.map((m) => ({ ...m, time: m.time as Time }))
    );

    // Volume series
    const volumeSeries = chart.addHistogramSeries({
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });

    chart.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });

    const volumeData = generateVolumeData(btcData);
    volumeSeries.setData(
      volumeData as unknown as { time: Time; value: number; color: string }[]
    );

    // Update price display
    const last = btcData[btcData.length - 1];
    const prev = btcData[btcData.length - 2];
    setLastPrice(last.close);
    setPriceChange(((last.close - prev.close) / prev.close) * 100);

    chart.timeScale().fitContent();
  }, [height, regime]);

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

  const isPositive = priceChange >= 0;

  return (
    <div className="w-full">
      {/* Price Header */}
      <div className="flex items-baseline gap-4 mb-4">
        <h2 className="text-2xl font-bold text-white">BTC/USD</h2>
        <span className="text-3xl font-mono font-bold text-white">
          ${lastPrice.toLocaleString("en-US", { minimumFractionDigits: 2 })}
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
      <div
        ref={containerRef}
        className="w-full rounded-lg overflow-hidden"
      />

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
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: REGIME_COLORS[regime] }} />
          Regime: {regime.replace("_", " ")}
        </span>
      </div>
    </div>
  );
}
