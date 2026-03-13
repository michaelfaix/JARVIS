// =============================================================================
// src/app/(app)/strategy-lab/page.tsx — Strategy Lab with Advanced Backtesting
// =============================================================================

"use client";

import { useCallback, useState } from "react";
import { HudPanel } from "@/components/ui/hud-panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { STRATEGIES } from "@/lib/constants";
import { useProfile } from "@/hooks/use-profile";
import { UpgradeGate } from "@/components/ui/upgrade-gate";
import {
  FlaskConical,
  Play,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Target,
  ShieldAlert,
  Clock,
  Zap,
  Loader2,
} from "lucide-react";
import {
  runBacktest,
  runWalkForward,
  STRATEGY_DESCRIPTIONS,
  type BacktestConfig,
  type BacktestResult,
  type WFVResult,
} from "@/lib/backtest-engine";
import { ComparisonTable, type BacktestResultSummary } from "@/components/strategy/comparison-table";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const AVAILABLE_ASSETS = ["BTC", "ETH", "SOL", "SPY", "GLD", "AAPL", "NVDA", "TSLA"];
const PERIOD_OPTIONS = [
  { label: "30d", value: 30 },
  { label: "90d", value: 90 },
  { label: "180d", value: 180 },
  { label: "1Y", value: 365 },
];
const DEFAULT_ASSETS = ["BTC", "ETH", "SOL", "SPY", "GLD"];

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

export default function StrategyLabPage() {
  const { tier } = useProfile();

  return (
    <UpgradeGate currentTier={tier} requiredTier="pro" feature="Strategy Lab & Backtesting">
      <StrategyLabContent />
    </UpgradeGate>
  );
}

// ---------------------------------------------------------------------------
// Strategy Lab Content
// ---------------------------------------------------------------------------

function StrategyLabContent() {
  // Config state
  const [selectedStrategy, setSelectedStrategy] = useState("combined");
  const [period, setPeriod] = useState(90);
  const [selectedAssets, setSelectedAssets] = useState<string[]>(DEFAULT_ASSETS);
  const [riskPerTrade, setRiskPerTrade] = useState(2);
  const [slPercent, setSlPercent] = useState(3);
  const [tpPercent, setTpPercent] = useState(6);

  // Results state
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [wfvResult, setWfvResult] = useState<WFVResult | null>(null);
  const [running, setRunning] = useState(false);
  const [runningWFV, setRunningWFV] = useState(false);
  const [comparisonHistory, setComparisonHistory] = useState<BacktestResultSummary[]>([]);

  const buildConfig = useCallback((): BacktestConfig => ({
    strategy: selectedStrategy,
    assets: selectedAssets.length > 0 ? selectedAssets : ["BTC"],
    period,
    initialCapital: 100000,
    riskPerTrade,
    slPercent,
    tpPercent,
  }), [selectedStrategy, selectedAssets, period, riskPerTrade, slPercent, tpPercent]);

  const handleBacktest = useCallback(() => {
    setRunning(true);
    setWfvResult(null);
    setTimeout(() => {
      const config = buildConfig();
      const r = runBacktest(config);
      setResult(r);
      setComparisonHistory((prev) => {
        const summary: BacktestResultSummary = {
          strategy: config.strategy,
          asset: config.assets.join(", "),
          period: config.period,
          totalReturn: r.totalReturn,
          winRate: r.winRate,
          sharpeRatio: r.sharpeRatio,
          maxDrawdown: r.maxDrawdown,
          profitFactor: r.profitFactor,
          totalTrades: r.trades.length,
          avgWin: r.avgWin,
          avgLoss: r.avgLoss,
        };
        const next = [...prev, summary];
        return next.slice(-5); // keep last 5
      });
      setRunning(false);
    }, 400);
  }, [buildConfig]);

  const handleWalkForward = useCallback(() => {
    setRunningWFV(true);
    setTimeout(() => {
      const config = buildConfig();
      const bt = runBacktest(config);
      setResult(bt);
      const wfv = runWalkForward(config, 5);
      setWfvResult(wfv);
      setRunningWFV(false);
    }, 600);
  }, [buildConfig]);

  const toggleAsset = useCallback((asset: string) => {
    setSelectedAssets((prev) =>
      prev.includes(asset)
        ? prev.filter((a) => a !== asset)
        : [...prev, asset]
    );
  }, []);

  return (
    <div className="p-2 sm:p-3 md:p-4 space-y-3">
      {/* Strategy Selection */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {STRATEGIES.map((strategy) => {
          const isSelected = selectedStrategy === strategy.id;
          return (
            <div
              key={strategy.id}
              onClick={() => setSelectedStrategy(strategy.id)}
              className={`bg-hud-bg/60 border rounded p-2.5 cursor-pointer transition-colors ${
                isSelected
                  ? "border-hud-cyan/50 ring-1 ring-hud-cyan/20"
                  : "border-hud-border/30 hover:border-hud-cyan/30"
              }`}
            >
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <FlaskConical
                    className={`h-4 w-4 ${
                      isSelected ? "text-hud-cyan" : "text-muted-foreground"
                    }`}
                  />
                  <span className="font-bold text-white text-sm font-mono">
                    {strategy.label}
                  </span>
                </div>
                <p className="text-[11px] text-muted-foreground leading-relaxed line-clamp-3">
                  {STRATEGY_DESCRIPTIONS[strategy.id] ?? ""}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Controls Panel */}
      <HudPanel title="BACKTEST CONFIGURATION">
        <div className="p-2.5">
          <div className="space-y-4">
            {/* Period Selection */}
            <div className="space-y-2">
              <div className="text-[10px] text-muted-foreground font-mono">PERIOD</div>
              <div className="flex gap-2">
                {PERIOD_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setPeriod(opt.value)}
                    className={`px-3 py-1.5 rounded text-xs font-mono transition-colors ${
                      period === opt.value
                        ? "bg-hud-cyan/20 text-hud-cyan border border-hud-cyan/30"
                        : "bg-hud-bg/60 text-muted-foreground border border-hud-border/30 hover:text-white hover:border-hud-border/50"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Asset Selection */}
            <div className="space-y-2">
              <div className="text-[10px] text-muted-foreground font-mono">ASSETS</div>
              <div className="flex flex-wrap gap-2">
                {AVAILABLE_ASSETS.map((asset) => {
                  const isChecked = selectedAssets.includes(asset);
                  return (
                    <button
                      key={asset}
                      onClick={() => toggleAsset(asset)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-mono transition-colors ${
                        isChecked
                          ? "bg-hud-cyan/20 text-hud-cyan border border-hud-cyan/30"
                          : "bg-hud-bg/60 text-muted-foreground border border-hud-border/30 hover:text-white hover:border-hud-border/50"
                      }`}
                    >
                      <div
                        className={`h-3 w-3 rounded-sm border flex items-center justify-center ${
                          isChecked ? "bg-hud-cyan border-hud-cyan" : "border-muted-foreground/50"
                        }`}
                      >
                        {isChecked && (
                          <svg viewBox="0 0 12 12" className="h-2 w-2 text-white">
                            <path
                              d="M2 6l3 3 5-5"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth={2}
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            />
                          </svg>
                        )}
                      </div>
                      {asset}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Risk Settings */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="space-y-2">
                <div className="text-[10px] text-muted-foreground font-mono">
                  RISK PER TRADE: <span className="font-mono text-white">{riskPerTrade}%</span>
                </div>
                <input
                  type="range"
                  min={1}
                  max={5}
                  step={0.5}
                  value={riskPerTrade}
                  onChange={(e) => setRiskPerTrade(parseFloat(e.target.value))}
                  className="w-full accent-hud-cyan"
                />
                <div className="flex justify-between text-[10px] text-muted-foreground font-mono">
                  <span>1%</span>
                  <span>5%</span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="text-[10px] text-muted-foreground font-mono">
                  STOP LOSS: <span className="font-mono text-white">{slPercent}%</span>
                </div>
                <input
                  type="range"
                  min={1}
                  max={10}
                  step={0.5}
                  value={slPercent}
                  onChange={(e) => setSlPercent(parseFloat(e.target.value))}
                  className="w-full accent-hud-red"
                />
                <div className="flex justify-between text-[10px] text-muted-foreground font-mono">
                  <span>1%</span>
                  <span>10%</span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="text-[10px] text-muted-foreground font-mono">
                  TAKE PROFIT: <span className="font-mono text-white">{tpPercent}%</span>
                </div>
                <input
                  type="range"
                  min={2}
                  max={20}
                  step={1}
                  value={tpPercent}
                  onChange={(e) => setTpPercent(parseFloat(e.target.value))}
                  className="w-full accent-hud-green"
                />
                <div className="flex justify-between text-[10px] text-muted-foreground font-mono">
                  <span>2%</span>
                  <span>20%</span>
                </div>
              </div>
            </div>

            <Separator className="opacity-30 border-hud-border/30" />

            {/* Action Buttons */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4 text-xs font-mono">
                <div>
                  <span className="text-muted-foreground">Strategy: </span>
                  <span className="text-white">
                    {STRATEGIES.find((s) => s.id === selectedStrategy)?.label}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground">Capital: </span>
                  <span className="text-white">$100,000</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Assets: </span>
                  <span className="text-white">{selectedAssets.length}</span>
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={handleBacktest}
                  disabled={running || runningWFV}
                  className="bg-hud-cyan/20 hover:bg-hud-cyan/30 text-hud-cyan border border-hud-cyan/30 gap-2"
                >
                  {running ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                  Run Backtest
                </Button>
                <Button
                  onClick={handleWalkForward}
                  disabled={running || runningWFV}
                  variant="outline"
                  className="border-hud-cyan/30 text-hud-cyan hover:bg-hud-cyan/10 gap-2"
                >
                  {runningWFV ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Zap className="h-4 w-4" />
                  )}
                  Run Walk-Forward
                </Button>
              </div>
            </div>
          </div>
        </div>
      </HudPanel>

      {/* Results */}
      {result && (
        <Tabs defaultValue="results">
          <TabsList className="bg-hud-bg/60 border border-hud-border/30">
            <TabsTrigger value="results" className="data-[state=active]:text-hud-cyan">Backtest Results</TabsTrigger>
            <TabsTrigger value="trades" className="data-[state=active]:text-hud-cyan">Trade Log</TabsTrigger>
            {wfvResult && <TabsTrigger value="wfv" className="data-[state=active]:text-hud-cyan">Walk-Forward</TabsTrigger>}
          </TabsList>

          {/* --- Backtest Results Tab --- */}
          <TabsContent value="results" className="space-y-3">
            {/* Summary Stats Grid (2x4) */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <StatCard
                label="Total Return"
                value={`${result.totalReturn >= 0 ? "+" : ""}${result.totalReturn.toFixed(2)}%`}
                color={result.totalReturn >= 0 ? "text-hud-green" : "text-hud-red"}
                icon={result.totalReturn >= 0 ? TrendingUp : TrendingDown}
              />
              <StatCard
                label="Win Rate"
                value={`${result.winRate.toFixed(1)}%`}
                color={result.winRate >= 50 ? "text-hud-green" : "text-hud-red"}
                icon={Target}
              />
              <StatCard
                label="Sharpe Ratio"
                value={result.sharpeRatio.toFixed(2)}
                color={
                  result.sharpeRatio > 1
                    ? "text-hud-green"
                    : result.sharpeRatio > 0
                    ? "text-hud-amber"
                    : "text-hud-red"
                }
                icon={BarChart3}
              />
              <StatCard
                label="Max Drawdown"
                value={`-${result.maxDrawdown.toFixed(2)}%`}
                color={result.maxDrawdown < 10 ? "text-hud-amber" : "text-hud-red"}
                icon={ShieldAlert}
              />
              <StatCard
                label="Avg Win"
                value={`+$${result.avgWin.toFixed(0)}`}
                color="text-hud-green"
                icon={TrendingUp}
              />
              <StatCard
                label="Avg Loss"
                value={`-$${result.avgLoss.toFixed(0)}`}
                color="text-hud-red"
                icon={TrendingDown}
              />
              <StatCard
                label="Profit Factor"
                value={result.profitFactor.toFixed(2)}
                color={
                  result.profitFactor > 1.5
                    ? "text-hud-green"
                    : result.profitFactor > 1
                    ? "text-hud-amber"
                    : "text-hud-red"
                }
                icon={Zap}
              />
              <StatCard
                label="Total Trades"
                value={result.totalTrades.toString()}
                color="text-white"
                icon={FlaskConical}
              />
            </div>

            {/* Additional Metrics Row */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              <StatCard
                label="Calmar Ratio"
                value={result.calmarRatio.toFixed(2)}
                color={result.calmarRatio > 1 ? "text-hud-green" : "text-hud-amber"}
                icon={Target}
              />
              <StatCard
                label="Avg Holding Period"
                value={`${result.avgHoldingPeriod.toFixed(1)}d`}
                color="text-hud-cyan"
                icon={Clock}
              />
              <StatCard
                label="Period"
                value={`${period} days`}
                color="text-muted-foreground"
                icon={Clock}
              />
            </div>

            {/* Equity Curve */}
            <EquityCurveChart result={result} />
          </TabsContent>

          {/* --- Trade Log Tab --- */}
          <TabsContent value="trades">
            <TradeLogTable trades={result.trades} />
          </TabsContent>

          {/* --- Walk-Forward Tab --- */}
          {wfvResult && (
            <TabsContent value="wfv" className="space-y-3">
              <WalkForwardPanel wfv={wfvResult} />
            </TabsContent>
          )}
        </Tabs>
      )}

      {/* Architecture Info */}
      <HudPanel title="JARVIS ARCHITECTURE">
        <div className="p-2.5">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div className="rounded-lg bg-hud-bg/60 border border-hud-border/30 p-3">
              <div className="text-[10px] text-muted-foreground mb-1 font-mono">ML MODULES</div>
              <div className="text-white font-bold font-mono">S06 — S15</div>
              <div className="text-muted-foreground mt-1">
                Fast Path, Deep Path, Uncertainty, Calibration, OOD, Quality,
                Learning, Degradation, API, Validation
              </div>
            </div>
            <div className="rounded-lg bg-hud-bg/60 border border-hud-border/30 p-3">
              <div className="text-[10px] text-muted-foreground mb-1 font-mono">DETERMINISM</div>
              <div className="text-white font-bold font-mono">DET-01 to DET-07</div>
              <div className="text-muted-foreground mt-1">
                No random, no file I/O, no global state, bit-identical outputs
              </div>
            </div>
            <div className="rounded-lg bg-hud-bg/60 border border-hud-border/30 p-3">
              <div className="text-[10px] text-muted-foreground mb-1 font-mono">TEST COVERAGE</div>
              <div className="text-white font-bold font-mono">8,897 Tests</div>
              <div className="text-muted-foreground mt-1">
                100% FAS compliance across all modules
              </div>
            </div>
            <div className="rounded-lg bg-hud-bg/60 border border-hud-border/30 p-3">
              <div className="text-[10px] text-muted-foreground mb-1 font-mono">RISK ENGINE</div>
              <div className="text-white font-bold font-mono">v6.1.0 FREEZE</div>
              <div className="text-muted-foreground mt-1">
                Hash-protected thresholds, DVH verified
              </div>
            </div>
          </div>
        </div>
      </HudPanel>

      {/* Strategy Comparison */}
      {comparisonHistory.length >= 2 && (
        <ComparisonTable results={comparisonHistory} />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Stat Card Component
// ---------------------------------------------------------------------------

function StatCard({
  label,
  value,
  color,
  icon: Icon,
}: {
  label: string;
  value: string;
  color: string;
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
      <div className="flex items-center gap-1 text-[10px] text-muted-foreground mb-1 font-mono">
        <Icon className="h-3 w-3" />
        {label.toUpperCase()}
      </div>
      <div className={`text-lg font-bold font-mono ${color}`}>{value}</div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Equity Curve Chart (SVG)
// ---------------------------------------------------------------------------

function EquityCurveChart({ result }: { result: BacktestResult }) {
  const points = result.equityCurve;
  if (points.length < 2) return null;

  const width = 700;
  const height = 220;
  const padding = { top: 20, right: 70, bottom: 30, left: 60 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const equities = points.map((p) => p.equity);
  const minY = Math.min(...equities) * 0.998;
  const maxY = Math.max(...equities) * 1.002;
  const rangeY = maxY - minY || 1;
  const maxDay = points[points.length - 1].day || 1;

  const toSvgX = (day: number) => padding.left + (day / maxDay) * chartW;
  const toSvgY = (eq: number) =>
    padding.top + chartH - ((eq - minY) / rangeY) * chartH;

  const linePath = points
    .map(
      (p, i) =>
        `${i === 0 ? "M" : "L"} ${toSvgX(p.day).toFixed(1)} ${toSvgY(p.equity).toFixed(1)}`
    )
    .join(" ");

  const areaPath = `${linePath} L ${toSvgX(maxDay).toFixed(1)} ${toSvgY(minY).toFixed(1)} L ${toSvgX(0).toFixed(1)} ${toSvgY(minY).toFixed(1)} Z`;

  const isPositive = result.totalReturn >= 0;
  const lineColor = isPositive ? "#22c55e" : "#ef4444";
  const fillColor = isPositive ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)";

  // Y-axis ticks (4 ticks)
  const yTicks = Array.from({ length: 4 }, (_, i) => minY + (rangeY * i) / 3);

  // Starting capital line
  const capitalY = toSvgY(100000);

  return (
    <HudPanel title="EQUITY CURVE">
      <div className="p-2.5">
        <div className="text-[10px] text-muted-foreground mb-2 font-mono">
          $100,000 starting capital
        </div>
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ maxHeight: height }}>
          {/* Grid lines */}
          {yTicks.map((tick, i) => (
            <g key={i}>
              <line
                x1={padding.left}
                x2={width - padding.right}
                y1={toSvgY(tick)}
                y2={toSvgY(tick)}
                stroke="currentColor"
                className="text-hud-border/30"
                strokeDasharray="4 4"
              />
              <text
                x={padding.left - 8}
                y={toSvgY(tick)}
                textAnchor="end"
                dominantBaseline="middle"
                className="fill-muted-foreground"
                fontSize={9}
                fontFamily="monospace"
              >
                ${(tick / 1000).toFixed(1)}k
              </text>
            </g>
          ))}

          {/* Starting capital reference line */}
          {capitalY >= padding.top && capitalY <= padding.top + chartH && (
            <line
              x1={padding.left}
              x2={width - padding.right}
              y1={capitalY}
              y2={capitalY}
              stroke="rgba(255,255,255,0.15)"
              strokeWidth={1}
              strokeDasharray="6 3"
            />
          )}

          {/* Area fill */}
          <path d={areaPath} fill={fillColor} />

          {/* Line */}
          <path d={linePath} fill="none" stroke={lineColor} strokeWidth={2} />

          {/* Data points (only first, last, and some intermediate) */}
          {points
            .filter(
              (_, i) =>
                i === 0 ||
                i === points.length - 1 ||
                i % Math.max(1, Math.floor(points.length / 12)) === 0
            )
            .map((p, i) => (
              <circle
                key={i}
                cx={toSvgX(p.day)}
                cy={toSvgY(p.equity)}
                r={i === 0 || p === points[points.length - 1] ? 3.5 : 2}
                fill={lineColor}
                opacity={0.8}
              />
            ))}

          {/* Start label */}
          <text
            x={toSvgX(0)}
            y={height - 8}
            textAnchor="start"
            className="fill-muted-foreground"
            fontSize={9}
          >
            Day 0
          </text>

          {/* End label */}
          <text
            x={toSvgX(maxDay)}
            y={height - 8}
            textAnchor="end"
            className="fill-muted-foreground"
            fontSize={9}
          >
            Day {maxDay}
          </text>

          {/* Final value label */}
          <text
            x={toSvgX(maxDay) + 4}
            y={toSvgY(equities[equities.length - 1])}
            dominantBaseline="middle"
            className="fill-white"
            fontSize={10}
            fontWeight="bold"
            fontFamily="monospace"
          >
            $
            {equities[equities.length - 1].toLocaleString("en-US", {
              maximumFractionDigits: 0,
            })}
          </text>
        </svg>
      </div>
    </HudPanel>
  );
}

// ---------------------------------------------------------------------------
// Trade Log Table
// ---------------------------------------------------------------------------

function TradeLogTable({ trades }: { trades: BacktestResult["trades"] }) {
  const displayed = trades.slice(0, 30);

  return (
    <HudPanel title="TRADE LOG">
      <div className="p-2.5">
        <div className="text-[10px] text-muted-foreground mb-3 font-mono">
          {trades.length} trades — showing last {displayed.length}
        </div>
        <div className="overflow-x-auto">
          <Table className="border-hud-border/30">
            <TableHeader>
              <TableRow className="border-hud-border/30">
                <TableHead className="text-[10px] font-mono">Day</TableHead>
                <TableHead className="text-[10px] font-mono">Asset</TableHead>
                <TableHead className="text-[10px] font-mono">Side</TableHead>
                <TableHead className="text-right text-[10px] font-mono">Entry</TableHead>
                <TableHead className="text-right text-[10px] font-mono">Exit</TableHead>
                <TableHead className="text-right text-[10px] font-mono">P&L</TableHead>
                <TableHead className="text-right text-[10px] font-mono">Return</TableHead>
                <TableHead className="text-center text-[10px] font-mono">Hold</TableHead>
                <TableHead className="text-center text-[10px] font-mono">Exit</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {displayed.map((trade, i) => (
                <TableRow key={i} className="border-hud-border/30">
                  <TableCell className="text-muted-foreground font-mono text-xs">
                    D{trade.day}
                  </TableCell>
                  <TableCell className="font-medium text-white font-mono">{trade.asset}</TableCell>
                  <TableCell>
                    <Badge
                      className={
                        trade.direction === "LONG"
                          ? "bg-hud-green/20 text-hud-green border-hud-green/30"
                          : "bg-hud-red/20 text-hud-red border-hud-red/30"
                      }
                    >
                      {trade.direction}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right font-mono text-muted-foreground text-xs">
                    ${trade.entry.toFixed(2)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-white text-xs">
                    ${trade.exit.toFixed(2)}
                  </TableCell>
                  <TableCell
                    className={`text-right font-mono ${
                      trade.pnl >= 0 ? "text-hud-green" : "text-hud-red"
                    }`}
                  >
                    {trade.pnl >= 0 ? "+" : ""}${Math.abs(trade.pnl).toFixed(0)}
                  </TableCell>
                  <TableCell
                    className={`text-right font-mono text-xs ${
                      trade.pnlPct >= 0 ? "text-hud-green" : "text-hud-red"
                    }`}
                  >
                    {trade.pnlPct >= 0 ? "+" : ""}
                    {trade.pnlPct.toFixed(2)}%
                  </TableCell>
                  <TableCell className="text-center font-mono text-xs text-muted-foreground">
                    {trade.holdingDays}d
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge
                      variant="outline"
                      className={`text-[10px] ${
                        trade.exitReason === "TP"
                          ? "text-hud-green border-hud-green/30"
                          : trade.exitReason === "SL"
                          ? "text-hud-red border-hud-red/30"
                          : "text-muted-foreground border-hud-border/50"
                      }`}
                    >
                      {trade.exitReason}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
        {trades.length > 30 && (
          <div className="text-xs text-muted-foreground text-center mt-3 font-mono">
            Showing 30 of {trades.length} trades
          </div>
        )}
      </div>
    </HudPanel>
  );
}

// ---------------------------------------------------------------------------
// Walk-Forward Validation Panel
// ---------------------------------------------------------------------------

function WalkForwardPanel({ wfv }: { wfv: WFVResult }) {
  return (
    <div className="space-y-3">
      {/* Robustness Badge + Aggregate Metrics */}
      <HudPanel title="WALK-FORWARD VALIDATION">
        <div className="p-2.5">
          <div className="flex items-center justify-between mb-3">
            <div className="text-[10px] text-muted-foreground font-mono flex items-center gap-2">
              <Zap className="h-4 w-4" />
              {wfv.windows.length} WINDOWS, 70/30 SPLIT
            </div>
            <Badge
              className={
                wfv.isRobust
                  ? "bg-hud-green/20 text-hud-green border-hud-green/30"
                  : "bg-hud-red/20 text-hud-red border-hud-red/30"
              }
            >
              {wfv.isRobust ? "Robust" : "Not Robust"}
            </Badge>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
              <div className="text-[10px] text-muted-foreground mb-1 font-mono">AGGREGATE RETURN</div>
              <div
                className={`text-lg font-bold font-mono ${
                  wfv.aggregateReturn >= 0 ? "text-hud-green" : "text-hud-red"
                }`}
              >
                {wfv.aggregateReturn >= 0 ? "+" : ""}
                {wfv.aggregateReturn.toFixed(2)}%
              </div>
            </div>
            <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
              <div className="text-[10px] text-muted-foreground mb-1 font-mono">AGGREGATE SHARPE</div>
              <div
                className={`text-lg font-bold font-mono ${
                  wfv.aggregateSharpe > 1
                    ? "text-hud-green"
                    : wfv.aggregateSharpe > 0
                    ? "text-hud-amber"
                    : "text-hud-red"
                }`}
              >
                {wfv.aggregateSharpe.toFixed(2)}
              </div>
            </div>
            <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
              <div className="text-[10px] text-muted-foreground mb-1 font-mono">PROFITABLE WINDOWS</div>
              <div className="text-lg font-bold font-mono text-white">
                {wfv.windows.filter((w) => w.totalReturn > 0).length}/{wfv.windows.length}
              </div>
            </div>
          </div>
        </div>
      </HudPanel>

      {/* Per-Window Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {wfv.windows.map((window) => (
          <HudPanel key={window.windowIndex}>
            <div className="p-2.5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-medium text-muted-foreground font-mono">
                  WINDOW {window.windowIndex + 1}
                </span>
                <Badge
                  variant="outline"
                  className={`text-[10px] ${
                    window.totalReturn >= 0
                      ? "text-hud-green border-hud-green/30"
                      : "text-hud-red border-hud-red/30"
                  }`}
                >
                  {window.totalReturn >= 0 ? "+" : ""}
                  {window.totalReturn.toFixed(1)}%
                </Badge>
              </div>
              <Separator className="opacity-20 border-hud-border/30" />
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted-foreground font-mono">Test Days</span>
                  <span className="font-mono text-white">
                    {window.testStart}—{window.testEnd}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground font-mono">Win Rate</span>
                  <span
                    className={`font-mono ${
                      window.winRate >= 50 ? "text-hud-green" : "text-hud-red"
                    }`}
                  >
                    {window.winRate.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground font-mono">Sharpe</span>
                  <span
                    className={`font-mono ${
                      window.sharpeRatio > 0 ? "text-hud-green" : "text-hud-red"
                    }`}
                  >
                    {window.sharpeRatio.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground font-mono">Trades</span>
                  <span className="font-mono text-white">{window.totalTrades}</span>
                </div>
              </div>
            </div>
          </HudPanel>
        ))}
      </div>
    </div>
  );
}
