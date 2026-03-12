// =============================================================================
// src/app/(app)/strategy-lab/page.tsx — Strategy Lab with Advanced Backtesting
// =============================================================================

"use client";

import { useCallback, useState } from "react";
import { AppHeader } from "@/components/layout/app-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
    <>
      <AppHeader title="Strategy Lab" subtitle="Backtest & Walk-Forward Validation" />
      <div className="p-3 sm:p-4 md:p-6 space-y-4 md:space-y-6">
        {/* Strategy Selection */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {STRATEGIES.map((strategy) => {
            const isSelected = selectedStrategy === strategy.id;
            return (
              <Card
                key={strategy.id}
                onClick={() => setSelectedStrategy(strategy.id)}
                className={`bg-card/50 border-border/50 cursor-pointer transition-colors ${
                  isSelected
                    ? "border-blue-500/50 ring-1 ring-blue-500/20"
                    : "hover:border-blue-500/30"
                }`}
              >
                <CardContent className="pt-4 pb-3 px-4 space-y-2">
                  <div className="flex items-center gap-2">
                    <FlaskConical
                      className={`h-4 w-4 ${
                        isSelected ? "text-blue-400" : "text-muted-foreground"
                      }`}
                    />
                    <span className="font-bold text-white text-sm">
                      {strategy.label}
                    </span>
                  </div>
                  <p className="text-[11px] text-muted-foreground leading-relaxed line-clamp-3">
                    {STRATEGY_DESCRIPTIONS[strategy.id] ?? ""}
                  </p>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Controls Panel */}
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Backtest Configuration
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Period Selection */}
            <div className="space-y-2">
              <div className="text-xs text-muted-foreground">Period</div>
              <div className="flex gap-2">
                {PERIOD_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setPeriod(opt.value)}
                    className={`px-3 py-1.5 rounded text-xs font-mono transition-colors ${
                      period === opt.value
                        ? "bg-blue-600 text-white"
                        : "bg-background/50 text-muted-foreground hover:text-white hover:bg-background/80"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Asset Selection */}
            <div className="space-y-2">
              <div className="text-xs text-muted-foreground">Assets</div>
              <div className="flex flex-wrap gap-2">
                {AVAILABLE_ASSETS.map((asset) => {
                  const isChecked = selectedAssets.includes(asset);
                  return (
                    <button
                      key={asset}
                      onClick={() => toggleAsset(asset)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-mono transition-colors ${
                        isChecked
                          ? "bg-blue-600/20 text-blue-400 border border-blue-500/30"
                          : "bg-background/50 text-muted-foreground border border-transparent hover:text-white hover:bg-background/80"
                      }`}
                    >
                      <div
                        className={`h-3 w-3 rounded-sm border flex items-center justify-center ${
                          isChecked ? "bg-blue-600 border-blue-500" : "border-muted-foreground/50"
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
                <div className="text-xs text-muted-foreground">
                  Risk per Trade: <span className="font-mono text-white">{riskPerTrade}%</span>
                </div>
                <input
                  type="range"
                  min={1}
                  max={5}
                  step={0.5}
                  value={riskPerTrade}
                  onChange={(e) => setRiskPerTrade(parseFloat(e.target.value))}
                  className="w-full accent-blue-500"
                />
                <div className="flex justify-between text-[10px] text-muted-foreground font-mono">
                  <span>1%</span>
                  <span>5%</span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="text-xs text-muted-foreground">
                  Stop Loss: <span className="font-mono text-white">{slPercent}%</span>
                </div>
                <input
                  type="range"
                  min={1}
                  max={10}
                  step={0.5}
                  value={slPercent}
                  onChange={(e) => setSlPercent(parseFloat(e.target.value))}
                  className="w-full accent-red-500"
                />
                <div className="flex justify-between text-[10px] text-muted-foreground font-mono">
                  <span>1%</span>
                  <span>10%</span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="text-xs text-muted-foreground">
                  Take Profit: <span className="font-mono text-white">{tpPercent}%</span>
                </div>
                <input
                  type="range"
                  min={2}
                  max={20}
                  step={1}
                  value={tpPercent}
                  onChange={(e) => setTpPercent(parseFloat(e.target.value))}
                  className="w-full accent-green-500"
                />
                <div className="flex justify-between text-[10px] text-muted-foreground font-mono">
                  <span>2%</span>
                  <span>20%</span>
                </div>
              </div>
            </div>

            <Separator className="opacity-30" />

            {/* Action Buttons */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4 text-xs">
                <div>
                  <span className="text-muted-foreground">Strategy: </span>
                  <span className="font-mono text-white">
                    {STRATEGIES.find((s) => s.id === selectedStrategy)?.label}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground">Capital: </span>
                  <span className="font-mono text-white">$100,000</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Assets: </span>
                  <span className="font-mono text-white">{selectedAssets.length}</span>
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={handleBacktest}
                  disabled={running || runningWFV}
                  className="bg-blue-600 hover:bg-blue-700 text-white gap-2"
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
                  className="border-blue-500/30 text-blue-400 hover:bg-blue-600/10 gap-2"
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
          </CardContent>
        </Card>

        {/* Results */}
        {result && (
          <Tabs defaultValue="results">
            <TabsList>
              <TabsTrigger value="results">Backtest Results</TabsTrigger>
              <TabsTrigger value="trades">Trade Log</TabsTrigger>
              {wfvResult && <TabsTrigger value="wfv">Walk-Forward</TabsTrigger>}
            </TabsList>

            {/* --- Backtest Results Tab --- */}
            <TabsContent value="results" className="space-y-4">
              {/* Summary Stats Grid (2x4) */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <StatCard
                  label="Total Return"
                  value={`${result.totalReturn >= 0 ? "+" : ""}${result.totalReturn.toFixed(2)}%`}
                  color={result.totalReturn >= 0 ? "text-green-400" : "text-red-400"}
                  icon={result.totalReturn >= 0 ? TrendingUp : TrendingDown}
                />
                <StatCard
                  label="Win Rate"
                  value={`${result.winRate.toFixed(1)}%`}
                  color={result.winRate >= 50 ? "text-green-400" : "text-red-400"}
                  icon={Target}
                />
                <StatCard
                  label="Sharpe Ratio"
                  value={result.sharpeRatio.toFixed(2)}
                  color={
                    result.sharpeRatio > 1
                      ? "text-green-400"
                      : result.sharpeRatio > 0
                      ? "text-yellow-400"
                      : "text-red-400"
                  }
                  icon={BarChart3}
                />
                <StatCard
                  label="Max Drawdown"
                  value={`-${result.maxDrawdown.toFixed(2)}%`}
                  color={result.maxDrawdown < 10 ? "text-yellow-400" : "text-red-400"}
                  icon={ShieldAlert}
                />
                <StatCard
                  label="Avg Win"
                  value={`+$${result.avgWin.toFixed(0)}`}
                  color="text-green-400"
                  icon={TrendingUp}
                />
                <StatCard
                  label="Avg Loss"
                  value={`-$${result.avgLoss.toFixed(0)}`}
                  color="text-red-400"
                  icon={TrendingDown}
                />
                <StatCard
                  label="Profit Factor"
                  value={result.profitFactor.toFixed(2)}
                  color={
                    result.profitFactor > 1.5
                      ? "text-green-400"
                      : result.profitFactor > 1
                      ? "text-yellow-400"
                      : "text-red-400"
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
                  color={result.calmarRatio > 1 ? "text-green-400" : "text-yellow-400"}
                  icon={Target}
                />
                <StatCard
                  label="Avg Holding Period"
                  value={`${result.avgHoldingPeriod.toFixed(1)}d`}
                  color="text-blue-400"
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
              <TabsContent value="wfv" className="space-y-4">
                <WalkForwardPanel wfv={wfvResult} />
              </TabsContent>
            )}
          </Tabs>
        )}

        {/* Architecture Info */}
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              JARVIS Architecture
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
              <div className="rounded-lg bg-background/50 p-3">
                <div className="text-muted-foreground mb-1">ML Modules</div>
                <div className="text-white font-bold">S06 — S15</div>
                <div className="text-muted-foreground mt-1">
                  Fast Path, Deep Path, Uncertainty, Calibration, OOD, Quality,
                  Learning, Degradation, API, Validation
                </div>
              </div>
              <div className="rounded-lg bg-background/50 p-3">
                <div className="text-muted-foreground mb-1">Determinism</div>
                <div className="text-white font-bold">DET-01 to DET-07</div>
                <div className="text-muted-foreground mt-1">
                  No random, no file I/O, no global state, bit-identical outputs
                </div>
              </div>
              <div className="rounded-lg bg-background/50 p-3">
                <div className="text-muted-foreground mb-1">Test Coverage</div>
                <div className="text-white font-bold">8,897 Tests</div>
                <div className="text-muted-foreground mt-1">
                  100% FAS compliance across all modules
                </div>
              </div>
              <div className="rounded-lg bg-background/50 p-3">
                <div className="text-muted-foreground mb-1">Risk Engine</div>
                <div className="text-white font-bold">v6.1.0 FREEZE</div>
                <div className="text-muted-foreground mt-1">
                  Hash-protected thresholds, DVH verified
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Strategy Comparison */}
        {comparisonHistory.length >= 2 && (
          <ComparisonTable results={comparisonHistory} />
        )}
      </div>
    </>
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
    <Card className="bg-card/50 border-border/50">
      <CardContent className="pt-3 pb-2 px-3">
        <div className="flex items-center gap-1 text-[10px] text-muted-foreground mb-1">
          <Icon className="h-3 w-3" />
          {label}
        </div>
        <div className={`text-lg font-bold font-mono ${color}`}>{value}</div>
      </CardContent>
    </Card>
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
    <Card className="bg-card/50 border-border/50">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Equity Curve — $100,000 starting capital
        </CardTitle>
      </CardHeader>
      <CardContent>
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
                className="text-border/30"
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
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Trade Log Table
// ---------------------------------------------------------------------------

function TradeLogTable({ trades }: { trades: BacktestResult["trades"] }) {
  const displayed = trades.slice(0, 30);

  return (
    <Card className="bg-card/50 border-border/50">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Trade Log ({trades.length} trades — showing last {displayed.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Day</TableHead>
                <TableHead>Asset</TableHead>
                <TableHead>Side</TableHead>
                <TableHead className="text-right">Entry</TableHead>
                <TableHead className="text-right">Exit</TableHead>
                <TableHead className="text-right">P&L</TableHead>
                <TableHead className="text-right">Return</TableHead>
                <TableHead className="text-center">Hold</TableHead>
                <TableHead className="text-center">Exit</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {displayed.map((trade, i) => (
                <TableRow key={i}>
                  <TableCell className="text-muted-foreground font-mono text-xs">
                    D{trade.day}
                  </TableCell>
                  <TableCell className="font-medium text-white">{trade.asset}</TableCell>
                  <TableCell>
                    <Badge
                      className={
                        trade.direction === "LONG"
                          ? "bg-green-500/20 text-green-400 border-green-500/30"
                          : "bg-red-500/20 text-red-400 border-red-500/30"
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
                      trade.pnl >= 0 ? "text-green-400" : "text-red-400"
                    }`}
                  >
                    {trade.pnl >= 0 ? "+" : ""}${Math.abs(trade.pnl).toFixed(0)}
                  </TableCell>
                  <TableCell
                    className={`text-right font-mono text-xs ${
                      trade.pnlPct >= 0 ? "text-green-400" : "text-red-400"
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
                          ? "text-green-400 border-green-500/30"
                          : trade.exitReason === "SL"
                          ? "text-red-400 border-red-500/30"
                          : "text-muted-foreground border-border/50"
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
          <div className="text-xs text-muted-foreground text-center mt-3">
            Showing 30 of {trades.length} trades
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Walk-Forward Validation Panel
// ---------------------------------------------------------------------------

function WalkForwardPanel({ wfv }: { wfv: WFVResult }) {
  return (
    <div className="space-y-4">
      {/* Robustness Badge + Aggregate Metrics */}
      <Card className="bg-card/50 border-border/50">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Walk-Forward Validation ({wfv.windows.length} windows, 70/30 split)
            </CardTitle>
            <Badge
              className={
                wfv.isRobust
                  ? "bg-green-500/20 text-green-400 border-green-500/30"
                  : "bg-red-500/20 text-red-400 border-red-500/30"
              }
            >
              {wfv.isRobust ? "Robust" : "Not Robust"}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <div className="text-xs text-muted-foreground mb-1">Aggregate Return</div>
              <div
                className={`text-lg font-bold font-mono ${
                  wfv.aggregateReturn >= 0 ? "text-green-400" : "text-red-400"
                }`}
              >
                {wfv.aggregateReturn >= 0 ? "+" : ""}
                {wfv.aggregateReturn.toFixed(2)}%
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Aggregate Sharpe</div>
              <div
                className={`text-lg font-bold font-mono ${
                  wfv.aggregateSharpe > 1
                    ? "text-green-400"
                    : wfv.aggregateSharpe > 0
                    ? "text-yellow-400"
                    : "text-red-400"
                }`}
              >
                {wfv.aggregateSharpe.toFixed(2)}
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Profitable Windows</div>
              <div className="text-lg font-bold font-mono text-white">
                {wfv.windows.filter((w) => w.totalReturn > 0).length}/{wfv.windows.length}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Per-Window Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {wfv.windows.map((window) => (
          <Card key={window.windowIndex} className="bg-card/50 border-border/50">
            <CardContent className="pt-3 pb-3 px-3 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-muted-foreground">
                  Window {window.windowIndex + 1}
                </span>
                <Badge
                  variant="outline"
                  className={`text-[10px] ${
                    window.totalReturn >= 0
                      ? "text-green-400 border-green-500/30"
                      : "text-red-400 border-red-500/30"
                  }`}
                >
                  {window.totalReturn >= 0 ? "+" : ""}
                  {window.totalReturn.toFixed(1)}%
                </Badge>
              </div>
              <Separator className="opacity-20" />
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Test Days</span>
                  <span className="font-mono text-white">
                    {window.testStart}—{window.testEnd}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Win Rate</span>
                  <span
                    className={`font-mono ${
                      window.winRate >= 50 ? "text-green-400" : "text-red-400"
                    }`}
                  >
                    {window.winRate.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Sharpe</span>
                  <span
                    className={`font-mono ${
                      window.sharpeRatio > 0 ? "text-green-400" : "text-red-400"
                    }`}
                  >
                    {window.sharpeRatio.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Trades</span>
                  <span className="font-mono text-white">{window.totalTrades}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
