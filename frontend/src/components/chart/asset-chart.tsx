// =============================================================================
// src/components/chart/asset-chart.tsx — Multi-Asset Candlestick Chart
//
// Crypto (BTC, ETH, SOL): Real Binance OHLC klines + live WebSocket candle.
// Other assets: Synthetic candlestick data.
// Uses TradingView Lightweight Charts with JARVIS signal overlay markers.
// =============================================================================

"use client";

import { useEffect, useRef, useState } from "react";
import {
  createChart,
  type IChartApi,
  type ISeriesApi,
  ColorType,
  type CandlestickData as LWCandlestickData,
  type Time,
} from "lightweight-charts";
import type { RegimeState } from "@/lib/types";
import { REGIME_COLORS } from "@/lib/types";
import { useBinanceKlines, type Kline } from "@/hooks/use-binance-klines";
import { useBinanceWsKline } from "@/hooks/use-binance-ws-kline";

// ---------------------------------------------------------------------------
// Synthetic data generation — for non-crypto assets
// ---------------------------------------------------------------------------

interface CandlePoint {
  time: number; // Unix timestamp in seconds (UTCTimestamp)
  open: number;
  high: number;
  low: number;
  close: number;
}

interface SignalMarker {
  time: number;
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

// Interval → { stepSeconds, count, volMultiplier, trendFreq, noiseFreq }
const TIMEFRAME_CONFIG: Record<
  string,
  {
    stepSeconds: number;
    count: number;
    volMul: number;
    trendFreq: number;
    noiseFreq: number;
  }
> = {
  "1m": {
    stepSeconds: 60,
    count: 60,
    volMul: 0.15,
    trendFreq: 8,
    noiseFreq: 12,
  },
  "5m": {
    stepSeconds: 300,
    count: 72,
    volMul: 0.3,
    trendFreq: 5,
    noiseFreq: 8,
  },
  "15m": {
    stepSeconds: 900,
    count: 96,
    volMul: 0.5,
    trendFreq: 3.5,
    noiseFreq: 5,
  },
  "1h": {
    stepSeconds: 3600,
    count: 90,
    volMul: 0.8,
    trendFreq: 2.5,
    noiseFreq: 3.5,
  },
  "4h": {
    stepSeconds: 14400,
    count: 90,
    volMul: 1.2,
    trendFreq: 2,
    noiseFreq: 2,
  },
  "1d": {
    stepSeconds: 86400,
    count: 90,
    volMul: 1.0,
    trendFreq: 1,
    noiseFreq: 1,
  },
  "1w": {
    stepSeconds: 604800,
    count: 52,
    volMul: 1.8,
    trendFreq: 0.5,
    noiseFreq: 0.4,
  },
};

function generateAssetData(
  symbol: string,
  basePrice: number,
  interval: string
): CandlePoint[] {
  const cfg = TIMEFRAME_CONFIG[interval] ?? TIMEFRAME_CONFIG["1d"];
  const data: CandlePoint[] = [];
  const seed = hashSymbol(symbol);
  const nowSec = Math.floor(Date.now() / 1000);
  const alignedNow = nowSec - (nowSec % cfg.stepSeconds);

  for (let i = cfg.count; i >= 0; i--) {
    const timestamp = alignedNow - i * cfg.stepSeconds;
    const idx = cfg.count - i;
    const t = idx / cfg.count;

    const trend =
      Math.sin(t * Math.PI * cfg.trendFreq + seed * 0.1) *
      basePrice *
      0.05 *
      cfg.volMul;
    const noise =
      Math.sin(idx * 0.7 * cfg.noiseFreq + seed) *
        basePrice *
        0.012 *
        cfg.volMul +
      Math.cos(idx * 1.3 * cfg.noiseFreq + seed * 0.5) *
        basePrice *
        0.006 *
        cfg.volMul;
    const price = basePrice + trend + noise;

    const volScale = basePrice * 0.008 * cfg.volMul;
    const volatility =
      volScale +
      Math.abs(Math.sin(idx * 0.3 * cfg.noiseFreq + seed)) * volScale * 3;
    const open =
      price + Math.sin(idx * 2.1 * cfg.noiseFreq + seed) * volatility * 0.3;
    const close =
      price + Math.cos(idx * 1.7 * cfg.noiseFreq + seed) * volatility * 0.3;
    const high =
      Math.max(open, close) +
      Math.abs(Math.sin(idx * 3.1 * cfg.noiseFreq + seed)) * volatility * 0.5;
    const low =
      Math.min(open, close) -
      Math.abs(Math.cos(idx * 2.7 * cfg.noiseFreq + seed)) * volatility * 0.5;

    data.push({
      time: timestamp,
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

function generateVolumeData(
  data: CandlePoint[],
  seed: number,
  klines?: Kline[]
) {
  return data.map((candle, i) => ({
    time: candle.time,
    value:
      klines?.[i]?.volume ??
      1000000 + Math.abs(Math.sin(i * 0.5 + seed)) * 5000000,
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
  onPriceChange?: (price: number) => void;
}

export function AssetChart({
  symbol,
  name,
  basePrice,
  livePrice,
  regime = "RISK_ON",
  height = 400,
  interval = "1d",
  onPriceChange,
}: AssetChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const [lastPrice, setLastPrice] = useState<number>(0);
  const [priceChange, setPriceChange] = useState<number>(0);
  const [wsLive, setWsLive] = useState(false);

  // Stable ref for the onPriceChange callback
  const onPriceChangeRef = useRef(onPriceChange);
  onPriceChangeRef.current = onPriceChange;

  // Keep track of previous close for % change
  const prevCloseRef = useRef<number>(0);

  const seed = hashSymbol(symbol);
  const { klines, isCrypto } = useBinanceKlines(symbol, interval);

  // Binance kline WebSocket — live candle updates for crypto
  const { tick, connected: wsKlineConnected } = useBinanceWsKline(
    symbol,
    interval
  );

  // Effect 1: Create the chart instance once
  useEffect(() => {
    if (!containerRef.current) return;

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
    candleSeriesRef.current = candleSeries;

    const volumeSeries = chart.addHistogramSeries({
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });
    chart.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });
    volumeSeriesRef.current = volumeSeries;

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
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
    };
  }, [symbol, interval, height]);

  // Effect 2: Load initial chart data when klines arrive
  useEffect(() => {
    if (!candleSeriesRef.current || !volumeSeriesRef.current) return;

    const assetData =
      isCrypto && klines.length > 0
        ? klinesToCandles(klines)
        : generateAssetData(symbol, basePrice, interval);

    candleSeriesRef.current.setData(
      assetData as unknown as LWCandlestickData<Time>[]
    );

    const markers = generateSignalMarkers(assetData, regime, seed);
    candleSeriesRef.current.setMarkers(
      markers.map((m) => ({ ...m, time: m.time as Time }))
    );

    const volumeData = generateVolumeData(
      assetData,
      seed,
      isCrypto && klines.length > 0 ? klines : undefined
    );
    volumeSeriesRef.current.setData(
      volumeData as unknown as { time: Time; value: number; color: string }[]
    );

    // Store previous close for % change
    const last = assetData[assetData.length - 1];
    const prev = assetData.length > 1 ? assetData[assetData.length - 2] : last;
    prevCloseRef.current = prev.close;
    setLastPrice(last.close);
    setPriceChange(((last.close - prev.close) / prev.close) * 100);

    if (chartRef.current) {
      chartRef.current.timeScale().fitContent();
    }
  }, [klines, isCrypto, symbol, basePrice, regime, seed, interval]);

  // Effect 3: Live candle update from WebSocket tick (crypto only)
  useEffect(() => {
    if (!tick || !candleSeriesRef.current || !volumeSeriesRef.current) return;

    setWsLive(wsKlineConnected);

    // Update the last (forming) candle in-place
    const liveCandle: LWCandlestickData<Time> = {
      time: tick.time as Time,
      open: tick.open,
      high: tick.high,
      low: tick.low,
      close: tick.close,
    };
    candleSeriesRef.current.update(liveCandle);

    // Update volume bar for the live candle
    volumeSeriesRef.current.update({
      time: tick.time as Time,
      value: tick.volume,
      color:
        tick.close >= tick.open
          ? "rgba(34, 197, 94, 0.3)"
          : "rgba(239, 68, 68, 0.3)",
    } as { time: Time; value: number; color: string });

    // Update price display
    setLastPrice(tick.close);
    if (prevCloseRef.current > 0) {
      setPriceChange(
        ((tick.close - prevCloseRef.current) / prevCloseRef.current) * 100
      );
    }

    // Notify parent of price change
    onPriceChangeRef.current?.(tick.close);
  }, [tick, wsKlineConnected]);

  // Effect 4: Simulated tick feed for non-crypto assets (1/s random walk)
  // Mimics a real tick feed with ±0.01–0.05% moves per second
  const simCandleRef = useRef<{
    time: number;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  } | null>(null);

  useEffect(() => {
    if (isCrypto) return; // crypto uses real WS
    if (!candleSeriesRef.current || !volumeSeriesRef.current) return;
    if (lastPrice <= 0) return; // wait for initial data

    // Initialize the simulated candle from the last candle
    const cfg = TIMEFRAME_CONFIG[interval] ?? TIMEFRAME_CONFIG["1d"];
    const nowSec = Math.floor(Date.now() / 1000);
    const candleTime = nowSec - (nowSec % cfg.stepSeconds);

    simCandleRef.current = {
      time: candleTime,
      open: lastPrice,
      high: lastPrice,
      low: lastPrice,
      close: lastPrice,
      volume: 500000 + Math.random() * 2000000,
    };

    const id = window.setInterval(() => {
      if (
        !simCandleRef.current ||
        !candleSeriesRef.current ||
        !volumeSeriesRef.current
      )
        return;

      const sc = simCandleRef.current;

      // Check if we need to start a new candle
      const now = Math.floor(Date.now() / 1000);
      const newCandleTime = now - (now % cfg.stepSeconds);
      if (newCandleTime > sc.time) {
        // Start a new candle; the old close becomes new open
        sc.time = newCandleTime;
        sc.open = sc.close;
        sc.high = sc.close;
        sc.low = sc.close;
        sc.volume = 500000 + Math.random() * 2000000;
      }

      // Random walk: ±0.01–0.05% per tick
      const pctMove = (Math.random() * 0.0004 + 0.0001) * (Math.random() > 0.5 ? 1 : -1);
      // Add slight mean-reversion toward basePrice
      const reversion = (basePrice - sc.close) / basePrice * 0.0002;
      const newPrice =
        Math.round((sc.close * (1 + pctMove + reversion)) * 100) / 100;

      sc.close = newPrice;
      sc.high = Math.max(sc.high, newPrice);
      sc.low = Math.min(sc.low, newPrice);
      sc.volume += 10000 + Math.random() * 50000;

      // Push to chart
      candleSeriesRef.current!.update({
        time: sc.time as Time,
        open: sc.open,
        high: sc.high,
        low: sc.low,
        close: sc.close,
      });

      volumeSeriesRef.current!.update({
        time: sc.time as Time,
        value: sc.volume,
        color:
          sc.close >= sc.open
            ? "rgba(34, 197, 94, 0.3)"
            : "rgba(239, 68, 68, 0.3)",
      } as { time: Time; value: number; color: string });

      // Update display
      setLastPrice(sc.close);
      if (prevCloseRef.current > 0) {
        setPriceChange(
          ((sc.close - prevCloseRef.current) / prevCloseRef.current) * 100
        );
      }

      onPriceChangeRef.current?.(sc.close);
    }, 1000);

    return () => {
      window.clearInterval(id);
      simCandleRef.current = null;
    };
    // Only restart when initial data loads (lastPrice changes from 0 to real value)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isCrypto, interval, lastPrice > 0, basePrice]);

  const displayPrice = livePrice ?? lastPrice;
  const isPositive = priceChange >= 0;

  return (
    <div className="w-full">
      {/* Price Header */}
      <div className="flex items-baseline gap-4 mb-4">
        <h2 className="text-2xl font-bold text-white">{symbol}/USD</h2>
        <span className="text-xs text-muted-foreground">{name}</span>
        {isCrypto && (wsLive || klines.length > 0) ? (
          <span
            className={`text-[10px] px-1.5 py-0.5 rounded ${
              wsLive
                ? "text-green-400 bg-green-500/10"
                : "text-blue-400 bg-blue-500/10"
            }`}
          >
            {wsLive ? "WS LIVE" : "REST DATA"}
          </span>
        ) : !isCrypto && simCandleRef.current ? (
          <span className="text-[10px] text-yellow-400 bg-yellow-500/10 px-1.5 py-0.5 rounded">
            SIM LIVE
          </span>
        ) : null}
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
