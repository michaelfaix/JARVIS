// =============================================================================
// src/components/dashboard/timeframe-slider.tsx — USP Timeframe Selector
//
// Slider from 1m to 1W — JARVIS auto-selects optimal strategy,
// recalculates entry/exit, and adapts regime detection.
// =============================================================================

"use client";

import { useCallback, useMemo } from "react";
import { Clock, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

export interface TimeframeConfig {
  label: string;
  value: string;
  minutes: number;
  strategy: "scalping" | "momentum" | "mean_reversion" | "combined";
  strategyLabel: string;
  description: string;
}

const TIMEFRAMES: TimeframeConfig[] = [
  {
    label: "1m",
    value: "1m",
    minutes: 1,
    strategy: "scalping",
    strategyLabel: "Scalping",
    description: "Ultra-fast entries, tight stops",
  },
  {
    label: "5m",
    value: "5m",
    minutes: 5,
    strategy: "scalping",
    strategyLabel: "Scalping",
    description: "Quick scalps, noise filtering",
  },
  {
    label: "15m",
    value: "15m",
    minutes: 15,
    strategy: "momentum",
    strategyLabel: "Momentum",
    description: "Short-term momentum capture",
  },
  {
    label: "1H",
    value: "1h",
    minutes: 60,
    strategy: "momentum",
    strategyLabel: "Momentum",
    description: "Intraday trend following",
  },
  {
    label: "4H",
    value: "4h",
    minutes: 240,
    strategy: "combined",
    strategyLabel: "Combined",
    description: "Balanced signals, swing entries",
  },
  {
    label: "1D",
    value: "1d",
    minutes: 1440,
    strategy: "combined",
    strategyLabel: "Combined",
    description: "Daily analysis, position trading",
  },
  {
    label: "1W",
    value: "1w",
    minutes: 10080,
    strategy: "mean_reversion",
    strategyLabel: "Mean Reversion",
    description: "Weekly reversals, wide targets",
  },
];

const STRATEGY_COLOR: Record<string, string> = {
  scalping: "text-purple-400",
  momentum: "text-blue-400",
  mean_reversion: "text-emerald-400",
  combined: "text-yellow-400",
};

const STRATEGY_BG: Record<string, string> = {
  scalping: "bg-purple-500",
  momentum: "bg-blue-500",
  mean_reversion: "bg-emerald-500",
  combined: "bg-yellow-500",
};

interface TimeframeSliderProps {
  value: number; // index 0-6
  onChange: (index: number) => void;
}

export function TimeframeSlider({ value, onChange }: TimeframeSliderProps) {
  const tf = TIMEFRAMES[value];

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onChange(parseInt(e.target.value, 10));
    },
    [onChange]
  );

  // Percentage for the gradient fill
  const pct = useMemo(() => (value / (TIMEFRAMES.length - 1)) * 100, [value]);

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium text-white">
            Timeframe
          </span>
          <span className="text-lg font-bold text-white">{tf.label}</span>
        </div>
        <div className="flex items-center gap-2">
          <Zap className={cn("h-3.5 w-3.5", STRATEGY_COLOR[tf.strategy])} />
          <span
            className={cn(
              "text-sm font-semibold",
              STRATEGY_COLOR[tf.strategy]
            )}
          >
            {tf.strategyLabel}
          </span>
        </div>
      </div>

      {/* Slider */}
      <div className="relative">
        <input
          type="range"
          min={0}
          max={TIMEFRAMES.length - 1}
          step={1}
          value={value}
          onChange={handleChange}
          className="w-full h-2 rounded-full appearance-none cursor-pointer
            [&::-webkit-slider-thumb]:appearance-none
            [&::-webkit-slider-thumb]:h-5
            [&::-webkit-slider-thumb]:w-5
            [&::-webkit-slider-thumb]:rounded-full
            [&::-webkit-slider-thumb]:border-2
            [&::-webkit-slider-thumb]:border-white
            [&::-webkit-slider-thumb]:shadow-lg
            [&::-moz-range-thumb]:h-5
            [&::-moz-range-thumb]:w-5
            [&::-moz-range-thumb]:rounded-full
            [&::-moz-range-thumb]:border-2
            [&::-moz-range-thumb]:border-white
            [&::-moz-range-thumb]:shadow-lg"
          style={{
            background: `linear-gradient(to right, hsl(var(--ring)) 0%, hsl(var(--ring)) ${pct}%, hsl(var(--muted)) ${pct}%, hsl(var(--muted)) 100%)`,
          }}
        />

        {/* Tick marks */}
        <div className="flex justify-between mt-1.5 px-0.5">
          {TIMEFRAMES.map((t, i) => (
            <button
              key={t.value}
              onClick={() => onChange(i)}
              className={cn(
                "text-[10px] transition-colors",
                i === value
                  ? "text-white font-bold"
                  : "text-muted-foreground hover:text-white"
              )}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Strategy info bar */}
      <div className="flex items-center gap-3 rounded-lg bg-background/50 border border-border/30 px-3 py-2">
        <div
          className={cn(
            "h-2 w-2 rounded-full shrink-0",
            STRATEGY_BG[tf.strategy]
          )}
        />
        <div className="flex-1">
          <span className="text-xs text-muted-foreground">
            {tf.description}
          </span>
        </div>
        <div className="text-[10px] text-muted-foreground font-mono">
          {tf.minutes < 60
            ? `${tf.minutes}min bars`
            : tf.minutes < 1440
            ? `${tf.minutes / 60}h bars`
            : tf.minutes < 10080
            ? `daily bars`
            : `weekly bars`}
        </div>
      </div>
    </div>
  );
}

export { TIMEFRAMES };
