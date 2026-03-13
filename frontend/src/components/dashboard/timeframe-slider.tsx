// =============================================================================
// src/components/dashboard/timeframe-slider.tsx — USP Timeframe Selector (HUD)
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
  { label: "1m", value: "1m", minutes: 1, strategy: "scalping", strategyLabel: "Scalping", description: "Ultra-fast entries, tight stops" },
  { label: "5m", value: "5m", minutes: 5, strategy: "scalping", strategyLabel: "Scalping", description: "Quick scalps, noise filtering" },
  { label: "15m", value: "15m", minutes: 15, strategy: "momentum", strategyLabel: "Momentum", description: "Short-term momentum capture" },
  { label: "1H", value: "1h", minutes: 60, strategy: "momentum", strategyLabel: "Momentum", description: "Intraday trend following" },
  { label: "4H", value: "4h", minutes: 240, strategy: "combined", strategyLabel: "Combined", description: "Balanced signals, swing entries" },
  { label: "1D", value: "1d", minutes: 1440, strategy: "combined", strategyLabel: "Combined", description: "Daily analysis, position trading" },
  { label: "1W", value: "1w", minutes: 10080, strategy: "mean_reversion", strategyLabel: "Mean Reversion", description: "Weekly reversals, wide targets" },
];

const STRATEGY_COLOR: Record<string, string> = {
  scalping: "text-purple-400",
  momentum: "text-hud-cyan",
  mean_reversion: "text-hud-green",
  combined: "text-hud-amber",
};

const STRATEGY_BG: Record<string, string> = {
  scalping: "bg-purple-500",
  momentum: "bg-hud-cyan",
  mean_reversion: "bg-hud-green",
  combined: "bg-hud-amber",
};

interface TimeframeSliderProps {
  value: number;
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

  const pct = useMemo(() => (value / (TIMEFRAMES.length - 1)) * 100, [value]);

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Clock className="h-3 w-3 text-muted-foreground" />
          <span className="text-[10px] font-mono text-muted-foreground">TF</span>
          <span className="text-xs font-bold font-mono text-white">{tf.label}</span>
          <div className={cn("h-1 w-1 rounded-full shrink-0 ml-1", STRATEGY_BG[tf.strategy])} />
          <span className={cn("text-[10px] font-mono font-semibold", STRATEGY_COLOR[tf.strategy])}>
            {tf.strategyLabel}
          </span>
        </div>
      </div>

      <div className="relative">
        <input
          type="range"
          min={0}
          max={TIMEFRAMES.length - 1}
          step={1}
          value={value}
          onChange={handleChange}
          className="w-full h-1 rounded-full appearance-none cursor-pointer
            [&::-webkit-slider-thumb]:appearance-none
            [&::-webkit-slider-thumb]:h-3.5
            [&::-webkit-slider-thumb]:w-3.5
            [&::-webkit-slider-thumb]:rounded-full
            [&::-webkit-slider-thumb]:border-2
            [&::-webkit-slider-thumb]:border-hud-cyan
            [&::-webkit-slider-thumb]:bg-hud-bg
            [&::-webkit-slider-thumb]:shadow-lg
            [&::-moz-range-thumb]:h-3.5
            [&::-moz-range-thumb]:w-3.5
            [&::-moz-range-thumb]:rounded-full
            [&::-moz-range-thumb]:border-2
            [&::-moz-range-thumb]:border-hud-cyan
            [&::-moz-range-thumb]:bg-hud-bg
            [&::-moz-range-thumb]:shadow-lg"
          style={{
            background: `linear-gradient(to right, #4db8ff 0%, #4db8ff ${pct}%, #0a1f35 ${pct}%, #0a1f35 100%)`,
          }}
        />
        <div className="flex justify-between mt-0.5 px-0.5">
          {TIMEFRAMES.map((t, i) => (
            <button
              key={t.value}
              onClick={() => onChange(i)}
              className={cn(
                "text-[8px] font-mono transition-colors",
                i === value ? "text-hud-cyan font-bold" : "text-muted-foreground/50 hover:text-hud-cyan"
              )}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export { TIMEFRAMES };
