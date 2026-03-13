// =============================================================================
// src/components/dashboard/strategy-control.tsx — Strategy Control Panel
//
// Dashboard widget: strategy selector, editable params, inline backtest,
// equity curve, custom rule builder. All client-side (no backend needed).
// =============================================================================

"use client";

import { useCallback, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  STRATEGY_PRESETS,
  type StrategyParams,
  type CustomRule,
  type StrategyState,
} from "@/hooks/use-strategy";
import type { BacktestResult } from "@/lib/backtest-engine";
import { DEFAULT_ASSETS } from "@/lib/constants";
import {
  Settings2,
  Play,
  TrendingUp,
  TrendingDown,
  Target,
  Shield,
  BarChart3,
  Plus,
  X,
  ChevronDown,
  ChevronUp,
  Loader2,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Param Editor
// ---------------------------------------------------------------------------

interface ParamRowProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  suffix?: string;
  onChange: (v: number) => void;
}

function ParamRow({ label, value, min, max, step, suffix = "", onChange }: ParamRowProps) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-[11px] text-muted-foreground w-20 shrink-0">{label}</span>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="flex-1 h-1.5 rounded-full appearance-none cursor-pointer bg-muted
          [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-3.5
          [&::-webkit-slider-thumb]:w-3.5 [&::-webkit-slider-thumb]:rounded-full
          [&::-webkit-slider-thumb]:bg-blue-500 [&::-webkit-slider-thumb]:border-2
          [&::-webkit-slider-thumb]:border-background
          [&::-moz-range-thumb]:h-3.5 [&::-moz-range-thumb]:w-3.5
          [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:bg-blue-500
          [&::-moz-range-thumb]:border-2 [&::-moz-range-thumb]:border-background"
      />
      <span className="text-[11px] font-mono text-white w-12 text-right">
        {value}{suffix}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Mini Equity Curve
// ---------------------------------------------------------------------------

function EquityCurve({ data, height = 80 }: { data: BacktestResult["equityCurve"]; height?: number }) {
  if (data.length < 2) return null;

  const w = 280;
  const h = height;
  const pad = 2;
  const equities = data.map((d) => d.equity);
  const min = Math.min(...equities);
  const max = Math.max(...equities);
  const range = max - min || 1;

  const points = data
    .map((d, i) => {
      const x = pad + (i / (data.length - 1)) * (w - pad * 2);
      const y = h - pad - ((d.equity - min) / range) * (h - pad * 2);
      return `${x},${y}`;
    })
    .join(" ");

  // Area fill
  const firstX = pad;
  const lastX = pad + ((data.length - 1) / (data.length - 1)) * (w - pad * 2);
  const areaPath = `M ${firstX},${h} L ${points.split(" ").map((p) => p).join(" L ")} L ${lastX},${h} Z`;

  const finalEquity = equities[equities.length - 1];
  const startEquity = equities[0];
  const positive = finalEquity >= startEquity;
  const color = positive ? "#4ade80" : "#f87171";

  return (
    <div className="w-full">
      <svg width="100%" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" className="rounded">
        {/* Reference line at start */}
        <line
          x1={pad}
          y1={h - pad - ((startEquity - min) / range) * (h - pad * 2)}
          x2={w - pad}
          y2={h - pad - ((startEquity - min) / range) * (h - pad * 2)}
          stroke="#ffffff10"
          strokeDasharray="4,4"
        />
        {/* Area */}
        <path d={areaPath} fill={`${color}15`} />
        {/* Line */}
        <polyline
          points={points}
          fill="none"
          stroke={color}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Backtest Results Panel
// ---------------------------------------------------------------------------

function BacktestResults({ result }: { result: BacktestResult }) {
  const metrics = [
    {
      label: "Win Rate",
      value: `${result.winRate.toFixed(1)}%`,
      icon: Target,
      color: result.winRate >= 50 ? "text-green-400" : "text-red-400",
    },
    {
      label: "Profit Factor",
      value: result.profitFactor >= 100 ? "∞" : result.profitFactor.toFixed(2),
      icon: TrendingUp,
      color: result.profitFactor >= 1.5 ? "text-green-400" : result.profitFactor >= 1 ? "text-yellow-400" : "text-red-400",
    },
    {
      label: "Max DD",
      value: `${result.maxDrawdown.toFixed(1)}%`,
      icon: Shield,
      color: result.maxDrawdown < 10 ? "text-green-400" : result.maxDrawdown < 20 ? "text-yellow-400" : "text-red-400",
    },
    {
      label: "Sharpe",
      value: result.sharpeRatio.toFixed(2),
      icon: BarChart3,
      color: result.sharpeRatio >= 1.5 ? "text-green-400" : result.sharpeRatio >= 0.5 ? "text-yellow-400" : "text-red-400",
    },
  ];

  const totalReturn = result.totalReturn;
  const returnColor = totalReturn >= 0 ? "text-green-400" : "text-red-400";

  return (
    <div className="space-y-3">
      {/* Total Return Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {totalReturn >= 0 ? (
            <TrendingUp className="h-4 w-4 text-green-400" />
          ) : (
            <TrendingDown className="h-4 w-4 text-red-400" />
          )}
          <span className={`text-lg font-bold font-mono ${returnColor}`}>
            {totalReturn >= 0 ? "+" : ""}{totalReturn.toFixed(2)}%
          </span>
        </div>
        <span className="text-[10px] text-muted-foreground">
          {result.totalTrades} trades
        </span>
      </div>

      {/* Equity Curve */}
      <EquityCurve data={result.equityCurve} />

      {/* Metric Chips */}
      <div className="grid grid-cols-2 gap-2">
        {metrics.map((m) => (
          <div key={m.label} className="flex items-center gap-1.5 rounded-lg bg-background/50 px-2.5 py-1.5">
            <m.icon className={`h-3 w-3 ${m.color}`} />
            <span className="text-[10px] text-muted-foreground">{m.label}</span>
            <span className={`text-[11px] font-mono font-bold ml-auto ${m.color}`}>
              {m.value}
            </span>
          </div>
        ))}
      </div>

      {/* Trade Distribution */}
      <div className="flex items-center gap-2 text-[10px]">
        <span className="text-muted-foreground">Avg Win:</span>
        <span className="font-mono text-green-400">${result.avgWin.toFixed(0)}</span>
        <span className="text-muted-foreground ml-2">Avg Loss:</span>
        <span className="font-mono text-red-400">${result.avgLoss.toFixed(0)}</span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Custom Rule Builder
// ---------------------------------------------------------------------------

const INDICATORS = ["RSI", "EMA_Fast", "EMA_Slow", "MACD", "Price", "Volume"];
const OPERATORS = [">", "<", ">=", "<=", "crosses_above", "crosses_below"] as const;

function RuleBuilder({
  rules,
  onAdd,
  onRemove,
}: {
  rules: CustomRule[];
  onAdd: (rule: CustomRule) => void;
  onRemove: (id: string) => void;
}) {
  const [indicator, setIndicator] = useState("RSI");
  const [operator, setOperator] = useState<CustomRule["operator"]>(">");
  const [value, setValue] = useState(70);
  const [action, setAction] = useState<"BUY" | "SELL">("BUY");

  const handleAdd = useCallback(() => {
    onAdd({
      id: `rule-${Date.now()}`,
      indicator,
      operator,
      value,
      logic: "AND",
      action,
    });
  }, [indicator, operator, value, action, onAdd]);

  return (
    <div className="space-y-2">
      <div className="text-[10px] text-muted-foreground font-medium">
        Custom Rules
      </div>

      {/* Existing rules */}
      {rules.map((rule) => (
        <div
          key={rule.id}
          className="flex items-center gap-1.5 rounded bg-background/50 px-2 py-1 text-[10px]"
        >
          <Badge className="text-[9px] bg-blue-500/20 text-blue-400 border-blue-500/30 px-1 py-0">
            IF
          </Badge>
          <span className="text-white font-medium">{rule.indicator}</span>
          <span className="text-muted-foreground">{rule.operator}</span>
          <span className="font-mono text-white">{rule.value}</span>
          <Badge
            className={`text-[9px] px-1 py-0 ${
              rule.action === "BUY"
                ? "bg-green-500/20 text-green-400 border-green-500/30"
                : "bg-red-500/20 text-red-400 border-red-500/30"
            }`}
          >
            {rule.action}
          </Badge>
          <button
            onClick={() => onRemove(rule.id)}
            className="ml-auto text-muted-foreground hover:text-red-400 transition-colors"
          >
            <X className="h-3 w-3" />
          </button>
        </div>
      ))}

      {/* Add rule row */}
      <div className="flex items-center gap-1.5 flex-wrap">
        <select
          value={indicator}
          onChange={(e) => setIndicator(e.target.value)}
          className="bg-background/80 border border-border/50 rounded px-1.5 py-0.5 text-[10px] text-white"
        >
          {INDICATORS.map((i) => (
            <option key={i} value={i}>{i}</option>
          ))}
        </select>
        <select
          value={operator}
          onChange={(e) => setOperator(e.target.value as CustomRule["operator"])}
          className="bg-background/80 border border-border/50 rounded px-1.5 py-0.5 text-[10px] text-white"
        >
          {OPERATORS.map((o) => (
            <option key={o} value={o}>{o}</option>
          ))}
        </select>
        <input
          type="number"
          value={value}
          onChange={(e) => setValue(parseFloat(e.target.value) || 0)}
          className="bg-background/80 border border-border/50 rounded px-1.5 py-0.5 text-[10px] text-white w-14 font-mono"
        />
        <select
          value={action}
          onChange={(e) => setAction(e.target.value as "BUY" | "SELL")}
          className="bg-background/80 border border-border/50 rounded px-1.5 py-0.5 text-[10px] text-white"
        >
          <option value="BUY">BUY</option>
          <option value="SELL">SELL</option>
        </select>
        <button
          onClick={handleAdd}
          className="flex items-center gap-0.5 rounded bg-blue-600/20 text-blue-400 border border-blue-500/30 px-1.5 py-0.5 text-[10px] hover:bg-blue-600/40 transition-colors"
        >
          <Plus className="h-2.5 w-2.5" />
          Add
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Widget
// ---------------------------------------------------------------------------

export interface StrategyControlProps {
  state: StrategyState;
  backtestResult: BacktestResult | null;
  backtesting: boolean;
  selectStrategy: (id: string) => void;
  updateParam: (key: keyof StrategyParams, value: number) => void;
  addRule: (rule: CustomRule) => void;
  removeRule: (id: string) => void;
  executeBacktest: (assets: string[], period: number) => void;
  /** When true, renders without Card wrapper (for embedding in unified layout) */
  embedded?: boolean;
}

export function StrategyControl({
  state,
  backtestResult,
  backtesting,
  selectStrategy,
  updateParam,
  addRule,
  removeRule,
  executeBacktest,
  embedded = false,
}: StrategyControlProps) {
  const [expanded, setExpanded] = useState(false);
  const [showRules, setShowRules] = useState(false);

  const currentPreset = useMemo(
    () => STRATEGY_PRESETS.find((p) => p.id === state.selectedStrategy),
    [state.selectedStrategy]
  );

  // Custom strategy validation: need at least 1 BUY + 1 SELL rule
  const customRulesValid = useMemo(() => {
    if (state.selectedStrategy !== "custom") return true;
    const hasBuy = state.customRules.some((r) => r.action === "BUY");
    const hasSell = state.customRules.some((r) => r.action === "SELL");
    return hasBuy && hasSell;
  }, [state.selectedStrategy, state.customRules]);

  const handleBacktest = useCallback(() => {
    const assets = DEFAULT_ASSETS.slice(0, 3).map((a) => a.symbol); // BTC, ETH, SOL
    executeBacktest(assets, 90); // 90 days
  }, [executeBacktest]);

  const content = (
    <div className={embedded ? "space-y-3" : "space-y-3 pb-4"}>
      {/* Header row */}
      <div className="flex items-center gap-2">
        <Settings2 className="h-3.5 w-3.5 text-muted-foreground" />
        <span className="text-[11px] font-medium text-muted-foreground">Strategy</span>
        {currentPreset && (
          <Badge className="text-[9px] bg-blue-500/20 text-blue-400 border-blue-500/30">
            {currentPreset.label}
          </Badge>
        )}
        <button
          onClick={() => setExpanded((p) => !p)}
          className="ml-auto text-muted-foreground hover:text-white transition-colors"
        >
          {expanded ? (
            <ChevronUp className="h-3.5 w-3.5" />
          ) : (
            <ChevronDown className="h-3.5 w-3.5" />
          )}
        </button>
      </div>

      {/* Strategy Selector — always visible */}
      <div className="flex flex-wrap gap-1">
        {STRATEGY_PRESETS.map((preset) => (
          <button
            key={preset.id}
            onClick={() => selectStrategy(preset.id)}
            className={`px-2 py-1 rounded-md text-[11px] font-medium transition-colors ${
              state.selectedStrategy === preset.id
                ? "bg-blue-600/20 text-blue-400 border border-blue-500/30"
                : "text-muted-foreground hover:bg-muted hover:text-foreground border border-transparent"
            }`}
            title={preset.description}
          >
            {preset.label}
          </button>
        ))}
      </div>

      {/* Description */}
      {currentPreset && (
        <p className="text-[10px] text-muted-foreground leading-relaxed">
          {currentPreset.description}
        </p>
      )}

      {/* Expanded: Parameters + Backtest */}
      {expanded && (
        <>
          {/* Parameter Sliders */}
          <div className="space-y-2 pt-1">
            <div className="text-[10px] text-muted-foreground font-medium">
              Parameters
            </div>
            <ParamRow
              label="RSI Length"
              value={state.params.rsiLength}
              min={5}
              max={30}
              step={1}
              onChange={(v) => updateParam("rsiLength", v)}
            />
            <ParamRow
              label="EMA Fast"
              value={state.params.emaFast}
              min={3}
              max={30}
              step={1}
              onChange={(v) => updateParam("emaFast", v)}
            />
            <ParamRow
              label="EMA Slow"
              value={state.params.emaSlow}
              min={10}
              max={100}
              step={1}
              onChange={(v) => updateParam("emaSlow", v)}
            />
            <ParamRow
              label="Stop Loss"
              value={state.params.slPercent}
              min={0.5}
              max={10}
              step={0.5}
              suffix="%"
              onChange={(v) => updateParam("slPercent", v)}
            />
            <ParamRow
              label="Take Profit"
              value={state.params.tpPercent}
              min={1}
              max={20}
              step={0.5}
              suffix="%"
              onChange={(v) => updateParam("tpPercent", v)}
            />
            <ParamRow
              label="Risk/Trade"
              value={state.params.riskPerTrade}
              min={0.5}
              max={5}
              step={0.5}
              suffix="%"
              onChange={(v) => updateParam("riskPerTrade", v)}
            />
          </div>

          {/* Custom Rules (only for Custom strategy) */}
          {state.selectedStrategy === "custom" && (
            <div className="pt-1">
              <button
                onClick={() => setShowRules((p) => !p)}
                className="text-[10px] text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1"
              >
                {showRules ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                {showRules ? "Hide" : "Show"} Rule Builder
              </button>
              {showRules && (
                <div className="mt-2">
                  <RuleBuilder
                    rules={state.customRules}
                    onAdd={addRule}
                    onRemove={removeRule}
                  />
                </div>
              )}
            </div>
          )}

          {/* Custom Rules Validation */}
          {state.selectedStrategy === "custom" && !customRulesValid && (
            <div className="text-[10px] text-yellow-400 bg-yellow-500/10 border border-yellow-500/20 rounded px-2.5 py-1.5">
              Add at least 1 BUY rule and 1 SELL rule to run backtest.
            </div>
          )}

          {/* Run Backtest Button */}
          <button
            onClick={handleBacktest}
            disabled={backtesting || (state.selectedStrategy === "custom" && !customRulesValid)}
            className="w-full flex items-center justify-center gap-2 rounded-lg bg-blue-600/20 text-blue-400 border border-blue-500/30 py-2 text-xs font-medium hover:bg-blue-600/40 transition-colors disabled:opacity-50"
          >
            {backtesting ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Play className="h-3.5 w-3.5" />
            )}
            {backtesting ? "Running..." : "Run Backtest (90d)"}
          </button>

          {/* Backtest Results */}
          {backtestResult && <BacktestResults result={backtestResult} />}
        </>
      )}
    </div>
  );

  if (embedded) return content;

  return (
    <Card className="bg-card/50 border-border/50">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          <Settings2 className="h-4 w-4" />
          Strategy Control
          {currentPreset && (
            <Badge className="ml-1 text-[9px] bg-blue-500/20 text-blue-400 border-blue-500/30">
              {currentPreset.label}
            </Badge>
          )}
          <button
            onClick={() => setExpanded((p) => !p)}
            className="ml-auto text-muted-foreground hover:text-white transition-colors"
          >
            {expanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </button>
        </CardTitle>
      </CardHeader>
      <CardContent>{content}</CardContent>
    </Card>
  );
}
