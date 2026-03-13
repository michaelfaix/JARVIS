// =============================================================================
// src/hooks/use-strategy.ts — Strategy selection, params & backtest state
// =============================================================================

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { loadJSON, saveJSON } from "@/lib/storage";
import {
  runBacktest,
  type BacktestConfig,
  type BacktestResult,
  type CustomRuleConfig,
} from "@/lib/backtest-engine";
import { DEFAULT_CAPITAL } from "@/lib/constants";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface StrategyPreset {
  id: string;
  label: string;
  description: string;
  params: StrategyParams;
}

export interface StrategyParams {
  rsiLength: number;
  emaFast: number;
  emaSlow: number;
  slPercent: number;
  tpPercent: number;
  riskPerTrade: number;
}

export interface CustomRule {
  id: string;
  indicator: string;
  operator: ">" | "<" | ">=" | "<=" | "crosses_above" | "crosses_below";
  value: number;
  logic: "AND" | "OR";
  action: "BUY" | "SELL";
}

export interface StrategyState {
  selectedStrategy: string;
  params: StrategyParams;
  customRules: CustomRule[];
}

// ---------------------------------------------------------------------------
// Presets
// ---------------------------------------------------------------------------

const DEFAULT_PARAMS: StrategyParams = {
  rsiLength: 14,
  emaFast: 12,
  emaSlow: 26,
  slPercent: 3,
  tpPercent: 6,
  riskPerTrade: 2,
};

export const STRATEGY_PRESETS: StrategyPreset[] = [
  {
    id: "scalping",
    label: "Scalping",
    description: "Ultra-fast entries, tight stops, high frequency",
    params: { rsiLength: 7, emaFast: 5, emaSlow: 13, slPercent: 1, tpPercent: 2, riskPerTrade: 1 },
  },
  {
    id: "day_trading",
    label: "Day Trading",
    description: "Intraday momentum capture with moderate risk",
    params: { rsiLength: 14, emaFast: 9, emaSlow: 21, slPercent: 2, tpPercent: 4, riskPerTrade: 2 },
  },
  {
    id: "swing_trading",
    label: "Swing Trading",
    description: "Multi-day holds, wider stops, trend confirmation",
    params: { rsiLength: 14, emaFast: 12, emaSlow: 26, slPercent: 4, tpPercent: 8, riskPerTrade: 2 },
  },
  {
    id: "trend_following",
    label: "Trend Following",
    description: "Ride long-term trends with trailing stops",
    params: { rsiLength: 21, emaFast: 20, emaSlow: 50, slPercent: 5, tpPercent: 15, riskPerTrade: 3 },
  },
  {
    id: "breakout",
    label: "Breakout",
    description: "Enter on confirmed breakouts from consolidation",
    params: { rsiLength: 14, emaFast: 10, emaSlow: 20, slPercent: 3, tpPercent: 9, riskPerTrade: 2 },
  },
  {
    id: "mean_reversion",
    label: "Mean Reversion",
    description: "Buy oversold, sell overbought — range-bound markets",
    params: { rsiLength: 10, emaFast: 8, emaSlow: 21, slPercent: 2, tpPercent: 4, riskPerTrade: 2 },
  },
  {
    id: "custom",
    label: "Custom",
    description: "Build your own strategy with custom rules",
    params: DEFAULT_PARAMS,
  },
];

// ---------------------------------------------------------------------------
// Storage
// ---------------------------------------------------------------------------

const STORAGE_KEY = "jarvis-strategy";

function defaultState(): StrategyState {
  return {
    selectedStrategy: "swing_trading",
    params: { ...STRATEGY_PRESETS[2].params },
    customRules: [],
  };
}

// ---------------------------------------------------------------------------
// Map our params to backtest engine config
// ---------------------------------------------------------------------------

function toBacktestConfig(
  state: StrategyState,
  assets: string[],
  period: number
): BacktestConfig {
  // Map our preset IDs to the backtest engine strategy names
  const engineMap: Record<string, string> = {
    scalping: "momentum",
    day_trading: "momentum",
    swing_trading: "combined",
    trend_following: "trend_following",
    breakout: "breakout",
    mean_reversion: "mean_reversion",
    custom: "combined",
  };

  const config: BacktestConfig = {
    strategy: engineMap[state.selectedStrategy] ?? "combined",
    assets,
    period,
    initialCapital: DEFAULT_CAPITAL,
    riskPerTrade: state.params.riskPerTrade,
    slPercent: state.params.slPercent,
    tpPercent: state.params.tpPercent,
    emaFast: state.params.emaFast,
    emaSlow: state.params.emaSlow,
    rsiLength: state.params.rsiLength,
  };

  // For custom strategy, pass rules to the engine
  if (state.selectedStrategy === "custom" && state.customRules.length > 0) {
    config.customRules = state.customRules.map((r): CustomRuleConfig => ({
      id: r.id,
      indicator: r.indicator,
      operator: r.operator,
      value: r.value,
      logic: r.logic,
      action: r.action,
    }));
  }

  return config;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useStrategy() {
  const [state, setState] = useState<StrategyState>(defaultState);
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [backtesting, setBacktesting] = useState(false);
  const initialLoadDone = useRef(false);

  // Load from localStorage on mount
  useEffect(() => {
    const loaded = loadJSON(STORAGE_KEY, defaultState());
    setState(loaded);
    initialLoadDone.current = true;
  }, []);

  // Persist on change
  useEffect(() => {
    if (!initialLoadDone.current) return;
    saveJSON(STORAGE_KEY, state);
  }, [state]);

  const selectStrategy = useCallback((id: string) => {
    const preset = STRATEGY_PRESETS.find((p) => p.id === id);
    setState((prev) => ({
      ...prev,
      selectedStrategy: id,
      params: preset ? { ...preset.params } : prev.params,
    }));
    setBacktestResult(null);
  }, []);

  const updateParam = useCallback(
    (key: keyof StrategyParams, value: number) => {
      setState((prev) => ({
        ...prev,
        params: { ...prev.params, [key]: value },
      }));
    },
    []
  );

  const addRule = useCallback((rule: CustomRule) => {
    setState((prev) => ({
      ...prev,
      customRules: [...prev.customRules, rule],
    }));
  }, []);

  const removeRule = useCallback((ruleId: string) => {
    setState((prev) => ({
      ...prev,
      customRules: prev.customRules.filter((r) => r.id !== ruleId),
    }));
  }, []);

  const executeBacktest = useCallback(
    (assets: string[], period: number) => {
      setBacktesting(true);
      // Use setTimeout to avoid blocking the UI
      setTimeout(() => {
        const config = toBacktestConfig(state, assets, period);
        const result = runBacktest(config);
        setBacktestResult(result);
        setBacktesting(false);
      }, 50);
    },
    [state]
  );

  return {
    state,
    backtestResult,
    backtesting,
    selectStrategy,
    updateParam,
    addRule,
    removeRule,
    executeBacktest,
  };
}
