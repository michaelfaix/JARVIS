// =============================================================================
// src/components/chart/asset-chart.tsx — Multi-Asset Candlestick Chart
//
// Crypto (BTC, ETH, SOL): Real Binance OHLC klines + live WebSocket candle.
// Other assets: Synthetic candlestick data.
// Uses TradingView Lightweight Charts with JARVIS signal overlay markers.
// =============================================================================

"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  createChart,
  type IChartApi,
  type ISeriesApi,
  ColorType,
  type Time,
  LineStyle,
} from "lightweight-charts";
import type { RegimeState } from "@/lib/types";
import { REGIME_COLORS } from "@/lib/types";
import { useBinanceKlines, type Kline } from "@/hooks/use-binance-klines";
import { useBinanceWsKline } from "@/hooks/use-binance-ws-kline";
import type { IndicatorConfig } from "@/components/chart/indicator-panel";
import {
  calcSMA,
  calcEMA,
  calcBollingerBands,
  calcRSI,
  calcMACD,
} from "@/lib/indicators";
import type { ChartDrawing, DrawingTool, DrawingPoint } from "@/hooks/use-chart-drawings";
import { DRAWING_COLORS } from "@/hooks/use-chart-drawings";

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

interface SignalEntry {
  index: number;
  time: number;
  price: number;
  direction: "LONG" | "SHORT";
}

function generateSignalMarkers(
  data: CandlePoint[],
  regime: RegimeState,
  seed: number,
  overlay?: StrategyOverlay,
): { markers: SignalMarker[]; signals: SignalEntry[] } {
  const markers: SignalMarker[] = [];
  const signals: SignalEntry[] = [];

  if (!overlay || data.length < 30) {
    // Fallback: simple momentum markers (no strategy context)
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
      signals.push({ index: i, time: candle.time, price: candle.close, direction: isBullish ? "LONG" : "SHORT" });
    }
  } else {
    // Strategy-aware signal generation using real indicators
    const rsiValues = calcRSI(data, overlay.rsiLength);
    const emaFastValues = calcEMA(data, overlay.emaFast);
    const emaSlowValues = calcEMA(data, overlay.emaSlow);

    const startIdx = Math.max(overlay.emaSlow, overlay.rsiLength) + 2;
    let lastSignalIdx = -5;

    for (let i = startIdx; i < data.length; i++) {
      if (i - lastSignalIdx < 3) continue; // minimum gap between signals

      const rsiVal = rsiValues[i];
      const emaF = emaFastValues[i];
      const emaS = emaSlowValues[i];
      const prevEmaF = emaFastValues[i - 1];
      const prevEmaS = emaSlowValues[i - 1];

      if (rsiVal === null || emaF === null || emaS === null || prevEmaF === null || prevEmaS === null) continue;

      let isBullish: boolean | null = null;

      switch (overlay.strategy) {
        case "scalping":
        case "day_trading":
          // EMA crossover signals
          if (prevEmaF <= prevEmaS && emaF > emaS) isBullish = true;
          if (prevEmaF >= prevEmaS && emaF < emaS) isBullish = false;
          break;
        case "mean_reversion":
          // RSI oversold/overbought
          if (rsiVal < 30) isBullish = true;
          if (rsiVal > 70) isBullish = false;
          break;
        case "trend_following":
          // EMA cross + RSI trend confirmation
          if (prevEmaF <= prevEmaS && emaF > emaS && rsiVal > 50) isBullish = true;
          if (prevEmaF >= prevEmaS && emaF < emaS && rsiVal < 50) isBullish = false;
          break;
        case "breakout": {
          // Price breaking above/below recent range
          let recentHigh = 0, recentLow = Infinity;
          const lookback = Math.min(14, i);
          for (let k = i - lookback; k < i; k++) {
            recentHigh = Math.max(recentHigh, data[k].high);
            recentLow = Math.min(recentLow, data[k].low);
          }
          if (data[i].close > recentHigh) isBullish = true;
          if (data[i].close < recentLow) isBullish = false;
          break;
        }
        case "swing_trading":
        case "combined":
        case "custom":
        default:
          // Combined: EMA cross + RSI confirmation
          if (prevEmaF <= prevEmaS && emaF > emaS && rsiVal < 65) isBullish = true;
          if (prevEmaF >= prevEmaS && emaF < emaS && rsiVal > 35) isBullish = false;
          break;
      }

      if (isBullish === null) continue;

      const candle = data[i];
      markers.push({
        time: candle.time,
        position: isBullish ? "belowBar" : "aboveBar",
        color: isBullish ? "#22c55e" : "#ef4444",
        shape: isBullish ? "arrowUp" : "arrowDown",
        text: isBullish ? "LONG" : "SHORT",
      });
      signals.push({
        index: i,
        time: candle.time,
        price: candle.close,
        direction: isBullish ? "LONG" : "SHORT",
      });
      lastSignalIdx = i;

      // EXIT marker: scan forward for SL/TP hit
      const exitScan = Math.min(i + 10, data.length - 1);
      const slPrice = isBullish
        ? candle.close * (1 - overlay.slPercent / 100)
        : candle.close * (1 + overlay.slPercent / 100);
      const tpPrice = isBullish
        ? candle.close * (1 + overlay.tpPercent / 100)
        : candle.close * (1 - overlay.tpPercent / 100);

      for (let j = i + 1; j <= exitScan; j++) {
        const hitSL = isBullish ? data[j].low <= slPrice : data[j].high >= slPrice;
        const hitTP = isBullish ? data[j].high >= tpPrice : data[j].low <= tpPrice;
        if (hitSL || hitTP) {
          markers.push({
            time: data[j].time,
            position: "aboveBar",
            color: hitTP ? "#22c55e" : "#ef4444",
            shape: "circle",
            text: hitTP ? "TP HIT" : "SL HIT",
          });
          break;
        }
        if (j === exitScan) {
          markers.push({
            time: data[j].time,
            position: "aboveBar",
            color: "#9ca3af",
            shape: "circle",
            text: "EXIT",
          });
        }
      }
    }
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

  // Sort markers by time (required by lightweight-charts)
  markers.sort((a, b) => a.time - b.time);

  return { markers, signals };
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
        ? "rgba(0, 230, 118, 0.15)"
        : "rgba(255, 61, 87, 0.15)",
  }));
}

// ---------------------------------------------------------------------------
// Indicator color map
// ---------------------------------------------------------------------------

const SMA_COLORS: Record<number, string> = {
  20: "#facc15",  // yellow
  50: "#06b6d4",  // cyan
  200: "#d946ef", // magenta
};

const EMA_COLORS: Record<number, string> = {
  12: "#f97316", // orange
  26: "#3b82f6", // blue
};

// ---------------------------------------------------------------------------
// Chart Component
// ---------------------------------------------------------------------------

export interface StrategyOverlay {
  strategy: string;
  slPercent: number;
  tpPercent: number;
  rsiLength: number;
  emaFast: number;
  emaSlow: number;
}

export interface JarvisTipsContext {
  regime: RegimeState;
  ece: number;
  oodScore: number;
  metaUncertainty: number;
  sentiment: number | null; // -1 to 1
  strategy: string;
}

interface ChartTip {
  text: string;
  type: "positive" | "warning" | "danger";
}

function generateChartTips(
  ctx: JarvisTipsContext,
  symbol: string,
  interval: string,
): ChartTip[] {
  const tips: ChartTip[] = [];
  const tf = interval === "1m" || interval === "5m" ? "kurzem" : interval === "1d" || interval === "1w" ? "langem" : "mittlerem";
  const strategyLabels: Record<string, string> = {
    momentum: "Momentum",
    mean_reversion: "Mean Reversion",
    combined: "Combined",
    breakout: "Breakout",
    trend_following: "Trend Following",
    scalping: "Scalping",
    swing_trading: "Swing Trading",
    custom: "Custom",
  };
  const stratLabel = strategyLabels[ctx.strategy] ?? ctx.strategy;

  // Regime-based
  if (ctx.regime === "RISK_ON") {
    tips.push({
      text: `${stratLabel} Strategie passt gut zum aktuellen Risk-On Markt — Long-Signale bevorzugen`,
      type: "positive",
    });
  } else if (ctx.regime === "RISK_OFF") {
    tips.push({
      text: `Risk-Off Markt erkannt — defensive Positionen und engere Stop-Losses empfohlen`,
      type: "warning",
    });
  } else if (ctx.regime === "CRISIS") {
    tips.push({
      text: `Krisenmodus aktiv — Positionsgroessen um 50% reduzieren oder absichern`,
      type: "danger",
    });
  } else if (ctx.regime === "TRANSITION") {
    tips.push({
      text: `Markt im Uebergang — auf Regime-Bestaetigung warten, bevor neue Positionen eroeffnet werden`,
      type: "warning",
    });
  }

  // ECE/OOD
  if (ctx.ece > 0.05) {
    tips.push({
      text: `Modell-Kalibrierung eingeschraenkt (${(ctx.ece * 100).toFixed(1)}%) — Konfidenzwerte mit Vorsicht interpretieren`,
      type: "warning",
    });
  }
  if (ctx.oodScore > 0.5) {
    tips.push({
      text: `Ungewoehnliche Marktbedingungen erkannt — Vorhersagen koennen unzuverlaessig sein`,
      type: ctx.oodScore > 0.8 ? "danger" : "warning",
    });
  }

  // Meta-uncertainty
  if (ctx.metaUncertainty > 0.3) {
    tips.push({
      text: `Hohe Unsicherheit erkannt — kleinere Positionen empfohlen`,
      type: "warning",
    });
  }

  // Strategy-sentiment alignment
  if (ctx.sentiment !== null) {
    if (ctx.sentiment < -0.3 && (ctx.strategy === "momentum" || ctx.strategy === "trend_following")) {
      tips.push({
        text: `Baerische Stimmung passt nicht zur ${stratLabel}-Strategie — Mean Reversion oder Exposure reduzieren`,
        type: "warning",
      });
    }
    if (ctx.sentiment > 0.3 && ctx.regime === "RISK_ON") {
      tips.push({
        text: `${symbol} zeigt starken Aufwaertstrend auf ${tf} Timeframe — Long-Signale bevorzugen`,
        type: "positive",
      });
    }
  }

  // Asset-specific
  if (symbol === "BTC" || symbol === "ETH" || symbol === "SOL") {
    if (ctx.regime === "RISK_ON") {
      tips.push({
        text: `Crypto profitiert ueberproportional im Risk-On — ${symbol} bietet gutes Momentum-Potential`,
        type: "positive",
      });
    }
  }
  if (symbol === "GLD" && ctx.regime === "CRISIS") {
    tips.push({
      text: `Gold als Safe Haven im Krisenmodus — GLD-Positionen koennen als Absicherung dienen`,
      type: "positive",
    });
  }

  // Default if no tips
  if (tips.length === 0) {
    tips.push({
      text: `Alle Systeme nominal — ${stratLabel} auf ${symbol} laeuft optimal`,
      type: "positive",
    });
  }

  return tips.slice(0, 3);
}

interface AssetChartProps {
  symbol: string;
  name: string;
  basePrice: number;
  livePrice?: number;
  regime?: RegimeState;
  height?: number;
  interval?: string;
  onPriceChange?: (price: number) => void;
  indicators?: IndicatorConfig;
  drawings?: ChartDrawing[];
  activeTool?: DrawingTool;
  onDrawingComplete?: (drawing: ChartDrawing) => void;
  strategyOverlay?: StrategyOverlay;
  jarvisTips?: JarvisTipsContext;
  chartType?: "line" | "candle" | "bar";
}

export function AssetChart({
  symbol,
  name: _name,
  basePrice,
  livePrice: _livePrice,
  regime = "RISK_ON",
  height = 400,
  interval = "1d",
  onPriceChange,
  indicators,
  drawings,
  activeTool = "none",
  onDrawingComplete,
  strategyOverlay,
  jarvisTips,
  chartType = "line",
}: AssetChartProps) {
  void _name; void _livePrice; // Props kept for API compat, display moved to JarvisChart
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [tipsOpen, setTipsOpen] = useState(false);
  const tipsRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const candleSeriesRef = useRef<ISeriesApi<any> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const [lastPrice, setLastPrice] = useState<number>(0);
  const [, setPriceChange] = useState<number>(0);
  const [, setWsLive] = useState(false);
  const [recalculating, setRecalculating] = useState(false);

  // Store candle data so marker effect can access it without reloading data
  const assetDataRef = useRef<CandlePoint[]>([]);

  // Indicator series refs — stored so we can remove them on re-render
  const indicatorSeriesRef = useRef<ISeriesApi<"Line">[]>([]);
  const indicatorHistogramRef = useRef<ISeriesApi<"Histogram">[]>([]);

  // Drawing series refs — kept separate from indicator series
  const drawingSeriesRef = useRef<ISeriesApi<"Line">[]>([]);

  // Strategy overlay series refs (SL/TP lines)
  const strategySeriesRef = useRef<ISeriesApi<"Line">[]>([]);

  // Pending drawing click state (first click of a two-click drawing)
  const pendingPointRef = useRef<DrawingPoint | null>(null);

  // Stable ref for the onPriceChange callback
  const onPriceChangeRef = useRef(onPriceChange);
  onPriceChangeRef.current = onPriceChange;

  // Stable ref for drawing callbacks
  const onDrawingCompleteRef = useRef(onDrawingComplete);
  onDrawingCompleteRef.current = onDrawingComplete;
  const activeToolRef = useRef(activeTool);
  activeToolRef.current = activeTool;

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
        background: { type: ColorType.Solid, color: "#05080f" },
        textColor: "#6b7f99",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "#0a1f35" },
        horzLines: { color: "#0a1f35" },
      },
      width: containerRef.current.clientWidth,
      height,
      crosshair: {
        vertLine: { color: "rgba(77, 184, 255, 0.3)" },
        horzLine: { color: "rgba(77, 184, 255, 0.3)" },
      },
      rightPriceScale: {
        borderColor: "#0a1f35",
      },
      timeScale: {
        borderColor: "#0a1f35",
        timeVisible: ["1m", "5m", "15m", "1h", "4h"].includes(interval),
      },
    });

    chartRef.current = chart;

    const candleSeries = chartType === "candle"
      ? chart.addCandlestickSeries({
          upColor: "#00e676", downColor: "#ff3d57",
          borderUpColor: "#00e676", borderDownColor: "#ff3d57",
          wickUpColor: "#00e67680", wickDownColor: "#ff3d5780",
        })
      : chartType === "bar"
        ? chart.addBarSeries({
            upColor: "#00e676", downColor: "#ff3d57",
          })
        : chart.addAreaSeries({
            lineColor: "#4a9eff", lineWidth: 2,
            topColor: "rgba(74,158,255,0.15)", bottomColor: "rgba(8,9,13,0)",
            crosshairMarkerRadius: 4,
            crosshairMarkerBorderColor: "#4a9eff",
            crosshairMarkerBackgroundColor: "#0d1117",
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

    // ResizeObserver: responds to container size changes (sidebar toggle, window resize)
    const ro = new ResizeObserver(() => {
      if (chartRef.current && containerRef.current) {
        chartRef.current.applyOptions({
          width: containerRef.current.clientWidth,
        });
      }
    });
    ro.observe(containerRef.current);

    return () => {
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
      indicatorSeriesRef.current = [];
      indicatorHistogramRef.current = [];
      drawingSeriesRef.current = [];
      strategySeriesRef.current = [];
    };
  }, [symbol, interval, height, chartType]);

  // Effect 2a: Load candle/volume data + indicator overlays (NOT strategy-dependent)
  useEffect(() => {
    if (!candleSeriesRef.current || !volumeSeriesRef.current || !chartRef.current) return;

    const chart = chartRef.current;

    // --- Remove previous indicator series ---
    for (const s of indicatorSeriesRef.current) {
      try { chart.removeSeries(s); } catch { /* already removed */ }
    }
    for (const s of indicatorHistogramRef.current) {
      try { chart.removeSeries(s); } catch { /* already removed */ }
    }
    indicatorSeriesRef.current = [];
    indicatorHistogramRef.current = [];

    // --- Set candle data ---
    const assetData =
      isCrypto && klines.length > 0
        ? klinesToCandles(klines)
        : generateAssetData(symbol, basePrice, interval);

    assetDataRef.current = assetData;

    // Line/area: { time, value }. Candle/bar: OHLC.
    if (chartType === "line") {
      candleSeriesRef.current.setData(
        assetData.map((d) => ({ time: d.time as unknown as Time, value: d.close }))
      );
    } else {
      candleSeriesRef.current.setData(
        assetData.map((d) => ({ time: d.time as unknown as Time, open: d.open, high: d.high, low: d.low, close: d.close }))
      );
    }

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

    // --- Indicator overlays ---
    if (indicators) {
      const times = assetData.map((d) => d.time);

      const addOverlayLine = (
        values: (number | null)[],
        color: string,
        lineWidth: number = 2,
        lineStyle: LineStyle = LineStyle.Solid
      ) => {
        const series = chart.addLineSeries({
          color,
          lineWidth: lineWidth as 1 | 2 | 3 | 4,
          lineStyle,
          priceScaleId: "right",
          lastValueVisible: false,
          priceLineVisible: false,
        });
        const lineData = values
          .map((v, i) =>
            v !== null ? { time: times[i] as Time, value: v } : null
          )
          .filter(Boolean) as { time: Time; value: number }[];
        series.setData(lineData);
        indicatorSeriesRef.current.push(series);
        return series;
      };

      for (const period of indicators.sma) {
        addOverlayLine(calcSMA(assetData, period), SMA_COLORS[period] ?? "#facc15");
      }
      for (const period of indicators.ema) {
        addOverlayLine(calcEMA(assetData, period), EMA_COLORS[period] ?? "#f97316");
      }
      if (indicators.bollinger) {
        const bb = calcBollingerBands(assetData, 20, 2);
        addOverlayLine(bb.upper, "rgba(156, 163, 175, 0.6)", 1, LineStyle.Dashed);
        addOverlayLine(bb.middle, "rgba(156, 163, 175, 0.8)", 1, LineStyle.Solid);
        addOverlayLine(bb.lower, "rgba(156, 163, 175, 0.6)", 1, LineStyle.Dashed);
      }
      if (indicators.rsi) {
        const rsiValues = calcRSI(assetData, 14);
        const rsiSeries = chart.addLineSeries({ color: "#a855f7", lineWidth: 2, priceScaleId: "rsi", lastValueVisible: true, priceLineVisible: false });
        chart.priceScale("rsi").applyOptions({ scaleMargins: { top: 0.78, bottom: 0.02 }, borderVisible: false });
        const rsiData = rsiValues.map((v, i) => v !== null ? { time: times[i] as Time, value: v } : null).filter(Boolean) as { time: Time; value: number }[];
        rsiSeries.setData(rsiData);
        indicatorSeriesRef.current.push(rsiSeries);
        for (const [level, color] of [[70, "rgba(239,68,68,0.3)"], [30, "rgba(34,197,94,0.3)"]] as const) {
          const lvlSeries = chart.addLineSeries({ color, lineWidth: 1, lineStyle: LineStyle.Dashed, priceScaleId: "rsi", lastValueVisible: false, priceLineVisible: false });
          const lvlData = rsiData.length > 0 ? [{ time: rsiData[0].time, value: level }, { time: rsiData[rsiData.length - 1].time, value: level }] : [];
          lvlSeries.setData(lvlData);
          indicatorSeriesRef.current.push(lvlSeries);
        }
      }
      if (indicators.macd) {
        const macd = calcMACD(assetData, 12, 26, 9);
        const macdHist = chart.addHistogramSeries({ priceScaleId: "macd", lastValueVisible: false, priceLineVisible: false });
        chart.priceScale("macd").applyOptions({ scaleMargins: { top: 0.85, bottom: 0.0 }, borderVisible: false });
        const histData = macd.histogram.map((v, i) => v !== null ? { time: times[i] as Time, value: v, color: v >= 0 ? "rgba(34,197,94,0.5)" : "rgba(239,68,68,0.5)" } : null).filter(Boolean) as { time: Time; value: number; color: string }[];
        macdHist.setData(histData);
        indicatorHistogramRef.current.push(macdHist);
        const macdLine = chart.addLineSeries({ color: "#06b6d4", lineWidth: 1, priceScaleId: "macd", lastValueVisible: false, priceLineVisible: false });
        macdLine.setData(macd.macd.map((v, i) => v !== null ? { time: times[i] as Time, value: v } : null).filter(Boolean) as { time: Time; value: number }[]);
        indicatorSeriesRef.current.push(macdLine);
        const sigLine = chart.addLineSeries({ color: "#f97316", lineWidth: 1, priceScaleId: "macd", lastValueVisible: false, priceLineVisible: false });
        sigLine.setData(macd.signal.map((v, i) => v !== null ? { time: times[i] as Time, value: v } : null).filter(Boolean) as { time: Time; value: number }[]);
        indicatorSeriesRef.current.push(sigLine);
      }
    }

    if (chartRef.current) {
      chartRef.current.timeScale().fitContent();
    }
  }, [klines, isCrypto, symbol, basePrice, seed, interval, indicators]);

  // Effect 2b: Update markers + SL/TP strategy overlay (reactive to strategy changes)
  // Runs independently of data loading — does NOT re-set candle data
  useEffect(() => {
    if (!candleSeriesRef.current || !chartRef.current) return;
    const chart = chartRef.current;
    const assetData = assetDataRef.current;
    if (assetData.length === 0) return;

    setRecalculating(true);

    // --- Remove previous strategy overlay series ---
    for (const s of strategySeriesRef.current) {
      try { chart.removeSeries(s); } catch { /* already removed */ }
    }
    strategySeriesRef.current = [];

    // Generate strategy-aware markers
    const { markers, signals } = generateSignalMarkers(assetData, regime, seed, strategyOverlay);
    candleSeriesRef.current.setMarkers(
      markers.map((m) => ({ ...m, time: m.time as Time }))
    );

    // --- Strategy Overlay: SL/TP lines for the most recent signal ---
    if (strategyOverlay && signals.length > 0) {
      const lastSignal = signals[signals.length - 1];
      const entryPrice = lastSignal.price;
      const isLong = lastSignal.direction === "LONG";

      const slPrice = isLong
        ? entryPrice * (1 - strategyOverlay.slPercent / 100)
        : entryPrice * (1 + strategyOverlay.slPercent / 100);
      const tpPrice = isLong
        ? entryPrice * (1 + strategyOverlay.tpPercent / 100)
        : entryPrice * (1 - strategyOverlay.tpPercent / 100);

      const tStart = lastSignal.time;
      const tEnd = assetData[assetData.length - 1].time + 86400 * 30;

      // SL line (red dashed)
      const slSeries = chart.addLineSeries({
        color: "#ef4444",
        lineWidth: 1,
        lineStyle: LineStyle.Dashed,
        priceScaleId: "right",
        lastValueVisible: true,
        priceLineVisible: false,
        title: `SL ${strategyOverlay.slPercent}%`,
      });
      slSeries.setData([
        { time: tStart as Time, value: slPrice },
        { time: tEnd as Time, value: slPrice },
      ]);
      strategySeriesRef.current.push(slSeries);

      // TP line (green dashed)
      const tpSeries = chart.addLineSeries({
        color: "#22c55e",
        lineWidth: 1,
        lineStyle: LineStyle.Dashed,
        priceScaleId: "right",
        lastValueVisible: true,
        priceLineVisible: false,
        title: `TP ${strategyOverlay.tpPercent}%`,
      });
      tpSeries.setData([
        { time: tStart as Time, value: tpPrice },
        { time: tEnd as Time, value: tpPrice },
      ]);
      strategySeriesRef.current.push(tpSeries);
    }

    // Brief flash then clear
    const tid = setTimeout(() => setRecalculating(false), 150);
    return () => clearTimeout(tid);
  }, [regime, seed, strategyOverlay]);

  // Effect 3: Live candle update from WebSocket tick (crypto only)
  useEffect(() => {
    if (!tick || !candleSeriesRef.current || !volumeSeriesRef.current) return;

    setWsLive(wsKlineConnected);

    // Update forming candle/point
    if (chartType === "line") {
      candleSeriesRef.current.update({ time: tick.time as Time, value: tick.close } as never);
    } else {
      candleSeriesRef.current.update({ time: tick.time as Time, open: tick.open, high: tick.high, low: tick.low, close: tick.close } as never);
    }

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
      if (chartType === "line") {
        candleSeriesRef.current!.update({ time: sc.time as Time, value: sc.close } as never);
      } else {
        candleSeriesRef.current!.update({ time: sc.time as Time, open: sc.open, high: sc.high, low: sc.low, close: sc.close } as never);
      }

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

  // Effect 5: Render drawing overlays on the chart
  useEffect(() => {
    if (!chartRef.current) return;
    const chart = chartRef.current;

    // Remove previous drawing series
    for (const s of drawingSeriesRef.current) {
      try { chart.removeSeries(s); } catch { /* already removed */ }
    }
    drawingSeriesRef.current = [];

    if (!drawings || drawings.length === 0) return;

    for (const drawing of drawings) {
      if (drawing.type === "horizontal" && drawing.points.length >= 1) {
        // Horizontal line: flat line across the entire visible range
        const price = drawing.points[0].price;
        const series = chart.addLineSeries({
          color: drawing.color,
          lineWidth: 1,
          lineStyle: LineStyle.Solid,
          priceScaleId: "right",
          lastValueVisible: true,
          priceLineVisible: false,
        });
        // Use the first and last candle times to span the chart
        // Use drawing point times to anchor, but extend across chart with two far-apart points
        const t = drawing.points[0].time;
        // Place line from far past to far future
        const tStart = t - 86400 * 365;
        const tEnd = t + 86400 * 365;
        series.setData([
          { time: tStart as Time, value: price },
          { time: tEnd as Time, value: price },
        ]);
        drawingSeriesRef.current.push(series);
      } else if (drawing.type === "trendline" && drawing.points.length >= 2) {
        // Trendline: line between two price/time points
        const series = chart.addLineSeries({
          color: drawing.color,
          lineWidth: 1,
          lineStyle: LineStyle.Solid,
          priceScaleId: "right",
          lastValueVisible: false,
          priceLineVisible: false,
        });
        series.setData([
          { time: drawing.points[0].time as Time, value: drawing.points[0].price },
          { time: drawing.points[1].time as Time, value: drawing.points[1].price },
        ]);
        drawingSeriesRef.current.push(series);
      } else if (drawing.type === "fibonacci" && drawing.points.length >= 2) {
        // Fibonacci retracement: horizontal lines at key levels between two prices
        const p1 = drawing.points[0].price;
        const p2 = drawing.points[1].price;
        const high = Math.max(p1, p2);
        const low = Math.min(p1, p2);
        const diff = high - low;

        const fibLevels = [0, 0.236, 0.382, 0.5, 0.618, 1.0];
        const t1 = Math.min(drawing.points[0].time, drawing.points[1].time);
        const t2 = Math.max(drawing.points[0].time, drawing.points[1].time);

        for (const level of fibLevels) {
          const price = high - diff * level;
          const series = chart.addLineSeries({
            color: drawing.color,
            lineWidth: 1,
            lineStyle: LineStyle.Dashed,
            priceScaleId: "right",
            lastValueVisible: false,
            priceLineVisible: false,
          });
          series.setData([
            { time: (t1 - 86400 * 30) as Time, value: price },
            { time: (t2 + 86400 * 30) as Time, value: price },
          ]);
          drawingSeriesRef.current.push(series);
        }
      } else if (drawing.type === "rectangle" && drawing.points.length >= 2) {
        // Rectangle: two horizontal lines for top and bottom bounds
        const p1 = drawing.points[0].price;
        const p2 = drawing.points[1].price;
        const t1 = Math.min(drawing.points[0].time, drawing.points[1].time);
        const t2 = Math.max(drawing.points[0].time, drawing.points[1].time);

        for (const price of [p1, p2]) {
          const series = chart.addLineSeries({
            color: drawing.color,
            lineWidth: 1,
            lineStyle: LineStyle.Solid,
            priceScaleId: "right",
            lastValueVisible: false,
            priceLineVisible: false,
          });
          series.setData([
            { time: t1 as Time, value: price },
            { time: t2 as Time, value: price },
          ]);
          drawingSeriesRef.current.push(series);
        }
      }
    }
  }, [drawings]);

  // Effect 6: Subscribe to chart clicks for placing drawings
  useEffect(() => {
    if (!chartRef.current) return;
    const chart = chartRef.current;

    const handleClick = (param: { time?: Time; point?: { x: number; y: number } }) => {
      const tool = activeToolRef.current;
      if (tool === "none" || !param.time || !param.point) return;
      if (!candleSeriesRef.current) return;

      // Get the price coordinate from the click Y position
      const price = candleSeriesRef.current.coordinateToPrice(param.point.y);
      if (price === null || price === undefined) return;

      const clickedTime = param.time as number;
      const point: DrawingPoint = { price: price as number, time: clickedTime };

      if (tool === "horizontal") {
        // Horizontal line only needs one click
        const drawing: ChartDrawing = {
          id: `drawing-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          type: "horizontal",
          points: [point],
          color: DRAWING_COLORS.horizontal,
          style: "solid",
        };
        pendingPointRef.current = null;
        onDrawingCompleteRef.current?.(drawing);
      } else {
        // Two-click tools: trendline, fibonacci, rectangle
        if (!pendingPointRef.current) {
          // First click — store the start point
          pendingPointRef.current = point;
        } else {
          // Second click — complete the drawing
          const drawing: ChartDrawing = {
            id: `drawing-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
            type: tool,
            points: [pendingPointRef.current, point],
            color: DRAWING_COLORS[tool as Exclude<DrawingTool, "none">],
            style: tool === "fibonacci" ? "dashed" : "solid",
          };
          pendingPointRef.current = null;
          onDrawingCompleteRef.current?.(drawing);
        }
      }
    };

    chart.subscribeClick(handleClick);

    return () => {
      chart.unsubscribeClick(handleClick);
    };
  }, [symbol, interval, height]); // Re-subscribe when chart recreates

  // Reset pending point when active tool changes
  useEffect(() => {
    pendingPointRef.current = null;
  }, [activeTool]);

  // --- JARVIS Tips: click-outside handler ---
  useEffect(() => {
    if (!tipsOpen) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (tipsRef.current && !tipsRef.current.contains(e.target as Node)) {
        setTipsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [tipsOpen]);

  const tips = useMemo(() => {
    if (!jarvisTips) return [];
    return generateChartTips(jarvisTips, symbol, interval);
  }, [jarvisTips, symbol, interval]);

  const toggleTips = useCallback(() => setTipsOpen((p) => !p), []);

  return (
    <div className="w-full">
      {/* Chart — header removed (JarvisChart provides it) */}
      <div className="relative">
        <div ref={containerRef} className="w-full rounded-lg overflow-hidden" />
        {recalculating && (
          <div className="absolute top-2 right-2 flex items-center gap-1.5 rounded bg-background/80 border border-border/50 px-2 py-1 text-[10px] text-blue-400 animate-pulse">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-ping" />
            Recalculating signals...
          </div>
        )}
        {/* JARVIS Tips Overlay */}
        {tipsOpen && tips.length > 0 && (
          <div
            ref={tipsRef}
            className="absolute top-2 right-2 z-10 w-72 rounded-xl
              bg-black/60 backdrop-blur-xl border border-white/10
              shadow-2xl shadow-black/40
              animate-in fade-in slide-in-from-top-2 duration-200"
          >
            <div className="px-3.5 py-2.5 border-b border-white/10 flex items-center justify-between">
              <span className="text-[11px] font-semibold text-white/90">JARVIS Tipps</span>
              <button
                onClick={toggleTips}
                className="text-white/40 hover:text-white/80 transition-colors text-xs"
              >
                &times;
              </button>
            </div>
            <div className="p-3 space-y-2">
              {tips.map((tip, i) => (
                <div
                  key={i}
                  className="flex items-start gap-2 rounded-lg bg-white/5 px-2.5 py-2"
                >
                  <span className={`mt-0.5 shrink-0 w-1.5 h-1.5 rounded-full ${
                    tip.type === "positive" ? "bg-green-400" :
                    tip.type === "warning" ? "bg-yellow-400" :
                    "bg-red-400"
                  }`} />
                  <span className="text-[11px] leading-relaxed text-white/80">
                    {tip.text}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex gap-3 sm:gap-6 mt-3 text-xs text-muted-foreground flex-wrap">
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-green-500" />
          LONG Signal
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-red-500" />
          SHORT Signal
        </span>
        {strategyOverlay && (
          <>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-red-500 opacity-50" />
              SL {strategyOverlay.slPercent}%
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-green-500 opacity-50" />
              TP {strategyOverlay.tpPercent}%
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-gray-400" />
              EXIT
            </span>
          </>
        )}
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
        {/* Active indicator legend */}
        {indicators?.sma.map((p) => (
          <span key={`sma-${p}`} className="flex items-center gap-1.5">
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: SMA_COLORS[p] ?? "#facc15" }}
            />
            SMA {p}
          </span>
        ))}
        {indicators?.ema.map((p) => (
          <span key={`ema-${p}`} className="flex items-center gap-1.5">
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: EMA_COLORS[p] ?? "#f97316" }}
            />
            EMA {p}
          </span>
        ))}
        {indicators?.bollinger && (
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-gray-400" />
            BB (20, 2)
          </span>
        )}
        {indicators?.rsi && (
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-purple-500" />
            RSI (14)
          </span>
        )}
        {indicators?.macd && (
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-cyan-500" />
            MACD
          </span>
        )}
      </div>
    </div>
  );
}
