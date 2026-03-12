// =============================================================================
// src/components/chart/indicator-panel.tsx — Indicator Selector Panel
//
// Compact dropdown panel for enabling/disabling technical indicators.
// Returns active indicator configuration via onChange callback.
// =============================================================================

"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export interface IndicatorConfig {
  sma: number[];        // active SMA periods (subset of [20, 50, 200])
  ema: number[];        // active EMA periods (subset of [12, 26])
  bollinger: boolean;
  rsi: boolean;
  macd: boolean;
}

export const DEFAULT_INDICATORS: IndicatorConfig = {
  sma: [],
  ema: [],
  bollinger: false,
  rsi: false,
  macd: false,
};

interface IndicatorPanelProps {
  value: IndicatorConfig;
  onChange: (config: IndicatorConfig) => void;
}

const SMA_OPTIONS = [
  { period: 20, color: "#facc15", label: "SMA 20" },
  { period: 50, color: "#06b6d4", label: "SMA 50" },
  { period: 200, color: "#d946ef", label: "SMA 200" },
];

const EMA_OPTIONS = [
  { period: 12, color: "#f97316", label: "EMA 12" },
  { period: 26, color: "#3b82f6", label: "EMA 26" },
];

export function IndicatorPanel({ value, onChange }: IndicatorPanelProps) {
  const [open, setOpen] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  // Close panel on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const activeCount =
    value.sma.length +
    value.ema.length +
    (value.bollinger ? 1 : 0) +
    (value.rsi ? 1 : 0) +
    (value.macd ? 1 : 0);

  const toggleSMA = (period: number) => {
    const next = value.sma.includes(period)
      ? value.sma.filter((p) => p !== period)
      : [...value.sma, period];
    onChange({ ...value, sma: next });
  };

  const toggleEMA = (period: number) => {
    const next = value.ema.includes(period)
      ? value.ema.filter((p) => p !== period)
      : [...value.ema, period];
    onChange({ ...value, ema: next });
  };

  return (
    <div className="relative" ref={panelRef}>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setOpen(!open)}
        className="h-8 px-2.5 text-[11px] gap-1.5"
      >
        Indicators
        {activeCount > 0 && (
          <Badge className="h-4 min-w-[16px] px-1 text-[9px] bg-blue-600/30 text-blue-400 border-blue-500/30">
            {activeCount}
          </Badge>
        )}
      </Button>

      {open && (
        <div className="absolute top-full left-0 mt-1 z-50 w-64 rounded-lg border border-border/50 bg-card/95 backdrop-blur-sm shadow-xl p-3 space-y-3">
          {/* Overlays heading */}
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">
            Overlays
          </div>

          {/* SMA */}
          <div className="space-y-1.5">
            <div className="text-xs text-muted-foreground">
              Simple Moving Average
            </div>
            <div className="flex gap-1.5 flex-wrap">
              {SMA_OPTIONS.map((opt) => (
                <button
                  key={opt.period}
                  onClick={() => toggleSMA(opt.period)}
                  className={`px-2 py-1 rounded text-[11px] font-medium transition-colors border ${
                    value.sma.includes(opt.period)
                      ? "border-opacity-50 bg-opacity-20"
                      : "border-border/30 text-muted-foreground hover:text-white hover:bg-muted"
                  }`}
                  style={
                    value.sma.includes(opt.period)
                      ? {
                          color: opt.color,
                          borderColor: opt.color,
                          backgroundColor: `${opt.color}20`,
                        }
                      : undefined
                  }
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* EMA */}
          <div className="space-y-1.5">
            <div className="text-xs text-muted-foreground">
              Exponential Moving Average
            </div>
            <div className="flex gap-1.5 flex-wrap">
              {EMA_OPTIONS.map((opt) => (
                <button
                  key={opt.period}
                  onClick={() => toggleEMA(opt.period)}
                  className={`px-2 py-1 rounded text-[11px] font-medium transition-colors border ${
                    value.ema.includes(opt.period)
                      ? "border-opacity-50 bg-opacity-20"
                      : "border-border/30 text-muted-foreground hover:text-white hover:bg-muted"
                  }`}
                  style={
                    value.ema.includes(opt.period)
                      ? {
                          color: opt.color,
                          borderColor: opt.color,
                          backgroundColor: `${opt.color}20`,
                        }
                      : undefined
                  }
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Bollinger */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">
              Bollinger Bands (20, 2)
            </span>
            <button
              onClick={() => onChange({ ...value, bollinger: !value.bollinger })}
              className={`px-2 py-1 rounded text-[11px] font-medium transition-colors border ${
                value.bollinger
                  ? "border-gray-400/50 bg-gray-400/20 text-gray-300"
                  : "border-border/30 text-muted-foreground hover:text-white hover:bg-muted"
              }`}
            >
              {value.bollinger ? "ON" : "OFF"}
            </button>
          </div>

          {/* Separator */}
          <div className="border-t border-border/30" />

          {/* Sub-panel indicators */}
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">
            Sub-Panels
          </div>

          {/* RSI */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">RSI (14)</span>
            <button
              onClick={() => onChange({ ...value, rsi: !value.rsi })}
              className={`px-2 py-1 rounded text-[11px] font-medium transition-colors border ${
                value.rsi
                  ? "border-purple-400/50 bg-purple-400/20 text-purple-300"
                  : "border-border/30 text-muted-foreground hover:text-white hover:bg-muted"
              }`}
            >
              {value.rsi ? "ON" : "OFF"}
            </button>
          </div>

          {/* MACD */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">
              MACD (12, 26, 9)
            </span>
            <button
              onClick={() => onChange({ ...value, macd: !value.macd })}
              className={`px-2 py-1 rounded text-[11px] font-medium transition-colors border ${
                value.macd
                  ? "border-cyan-400/50 bg-cyan-400/20 text-cyan-300"
                  : "border-border/30 text-muted-foreground hover:text-white hover:bg-muted"
              }`}
            >
              {value.macd ? "ON" : "OFF"}
            </button>
          </div>

          {/* Clear all */}
          {activeCount > 0 && (
            <>
              <div className="border-t border-border/30" />
              <button
                onClick={() => onChange({ ...DEFAULT_INDICATORS })}
                className="text-[11px] text-red-400 hover:text-red-300 transition-colors"
              >
                Clear All
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
