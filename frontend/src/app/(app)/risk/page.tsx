// =============================================================================
// src/app/(app)/risk/page.tsx — Risk Guardian
// =============================================================================

"use client";

import { useEffect } from "react";
import { AppHeader } from "@/components/layout/app-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { usePortfolio } from "@/hooks/use-portfolio";
import { useSystemStatus } from "@/hooks/use-jarvis";
import { usePrices } from "@/hooks/use-prices";
import { inferRegime, REGIME_COLORS, type RegimeState } from "@/lib/types";
import { CorrelationMatrix } from "@/components/risk/correlation-matrix";
import { PositionCalculator } from "@/components/risk/position-calculator";
import { RiskScoreGauge } from "@/components/risk/risk-score-gauge";
import { DEFAULT_ASSETS } from "@/lib/constants";
import {
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  AlertTriangle,
  TrendingDown,
  Target,
  Layers,
  BarChart3,
  Grid3X3,
} from "lucide-react";

// Risk thresholds
const MAX_SINGLE_EXPOSURE_PCT = 25; // Max 25% in one asset
const MAX_DRAWDOWN_PCT = 10; // Warn at 10% drawdown
const MAX_OPEN_POSITIONS = 6; // Max concurrent positions
const MIN_AVAILABLE_CAPITAL_PCT = 20; // Keep 20% cash reserve

type RiskLevel = "safe" | "warning" | "danger";

interface RiskCheck {
  label: string;
  description: string;
  value: number;
  limit: number;
  unit: string;
  level: RiskLevel;
  icon: typeof ShieldCheck;
}

export default function RiskPage() {
  const {
    state,
    totalValue,
    updatePrices,
    drawdown,
    maxSingleExposurePct,
    exposureByAsset,
    winRate,
  } = usePortfolio();
  const { status } = useSystemStatus(5000);
  const regime: RegimeState = status ? inferRegime(status.modus) : "RISK_ON";
  const { prices } = usePrices(5000);

  useEffect(() => {
    if (state.positions.length > 0) {
      updatePrices(prices);
    }
  }, [prices, state.positions.length, updatePrices]);

  const availablePct =
    totalValue > 0 ? (state.availableCapital / totalValue) * 100 : 100;

  // Build risk checks
  const checks: RiskCheck[] = [
    {
      label: "Single Asset Exposure",
      description: `Largest position: ${maxSingleExposurePct.toFixed(1)}% of portfolio (limit: ${MAX_SINGLE_EXPOSURE_PCT}%)`,
      value: maxSingleExposurePct,
      limit: MAX_SINGLE_EXPOSURE_PCT,
      unit: "%",
      level:
        maxSingleExposurePct > MAX_SINGLE_EXPOSURE_PCT
          ? "danger"
          : maxSingleExposurePct > MAX_SINGLE_EXPOSURE_PCT * 0.8
          ? "warning"
          : "safe",
      icon: Target,
    },
    {
      label: "Portfolio Drawdown",
      description: `Current drawdown: ${drawdown.toFixed(2)}% from peak (limit: ${MAX_DRAWDOWN_PCT}%)`,
      value: drawdown,
      limit: MAX_DRAWDOWN_PCT,
      unit: "%",
      level:
        drawdown > MAX_DRAWDOWN_PCT
          ? "danger"
          : drawdown > MAX_DRAWDOWN_PCT * 0.7
          ? "warning"
          : "safe",
      icon: TrendingDown,
    },
    {
      label: "Open Positions",
      description: `${state.positions.length} of ${MAX_OPEN_POSITIONS} maximum positions`,
      value: state.positions.length,
      limit: MAX_OPEN_POSITIONS,
      unit: "",
      level:
        state.positions.length >= MAX_OPEN_POSITIONS
          ? "danger"
          : state.positions.length >= MAX_OPEN_POSITIONS - 1
          ? "warning"
          : "safe",
      icon: Layers,
    },
    {
      label: "Cash Reserve",
      description: `${availablePct.toFixed(1)}% available (minimum: ${MIN_AVAILABLE_CAPITAL_PCT}%)`,
      value: 100 - availablePct, // Invert: higher = more risk
      limit: 100 - MIN_AVAILABLE_CAPITAL_PCT,
      unit: "%",
      level:
        availablePct < MIN_AVAILABLE_CAPITAL_PCT
          ? "danger"
          : availablePct < MIN_AVAILABLE_CAPITAL_PCT * 1.5
          ? "warning"
          : "safe",
      icon: BarChart3,
    },
  ];

  const dangerCount = checks.filter((c) => c.level === "danger").length;
  const warningCount = checks.filter((c) => c.level === "warning").length;
  const overallLevel: RiskLevel =
    dangerCount > 0 ? "danger" : warningCount > 0 ? "warning" : "safe";

  const levelColors = {
    safe: "text-green-400",
    warning: "text-yellow-400",
    danger: "text-red-400",
  };
  const levelBg = {
    safe: "bg-green-500/10 border-green-500/20",
    warning: "bg-yellow-500/10 border-yellow-500/20",
    danger: "bg-red-500/10 border-red-500/20",
  };
  const levelLabels = {
    safe: "All Clear",
    warning: "Caution",
    danger: "Action Required",
  };
  const LevelIcon =
    overallLevel === "safe"
      ? ShieldCheck
      : overallLevel === "warning"
      ? ShieldAlert
      : ShieldX;

  return (
    <>
      <AppHeader title="Risk Guardian" subtitle="Portfolio Risk Monitor" />
      <div className="p-3 sm:p-4 md:p-6 space-y-4 md:space-y-6">
        {/* Overall Status */}
        <Card className={`border ${levelBg[overallLevel]}`}>
          <CardContent className="pt-5 pb-4 px-6">
            <div className="flex items-center gap-4">
              <LevelIcon className={`h-10 w-10 ${levelColors[overallLevel]}`} />
              <div>
                <div className={`text-2xl font-bold ${levelColors[overallLevel]}`}>
                  {levelLabels[overallLevel]}
                </div>
                <div className="text-sm text-muted-foreground">
                  {dangerCount === 0 && warningCount === 0
                    ? "All risk checks passed. Portfolio is within safe parameters."
                    : `${dangerCount} critical, ${warningCount} warning${warningCount !== 1 ? "s" : ""}`}
                </div>
              </div>
              <div className="ml-auto flex items-center gap-3">
                <Badge
                  variant="outline"
                  className="text-xs"
                  style={{
                    borderColor: REGIME_COLORS[regime],
                    color: REGIME_COLORS[regime],
                  }}
                >
                  {regime.replace("_", " ")}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Risk Score Gauge */}
        <RiskScoreGauge
          score={Math.min(100, Math.round(
            (maxSingleExposurePct / MAX_SINGLE_EXPOSURE_PCT) * 25 +
            (drawdown / MAX_DRAWDOWN_PCT) * 25 +
            (state.positions.length / MAX_OPEN_POSITIONS) * 25 +
            ((100 - availablePct) / (100 - MIN_AVAILABLE_CAPITAL_PCT)) * 25
          ))}
          maxExposure={maxSingleExposurePct}
          openPositions={state.positions.length}
          drawdown={drawdown}
        />

        {/* Risk Checks Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {checks.map((check) => {
            const Icon = check.icon;
            const pct = Math.min((check.value / check.limit) * 100, 100);
            return (
              <Card key={check.label} className="bg-card/50 border-border/50">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Icon className={`h-4 w-4 ${levelColors[check.level]}`} />
                    <span className="text-muted-foreground">{check.label}</span>
                    <Badge
                      className={`ml-auto text-[10px] ${
                        check.level === "safe"
                          ? "bg-green-500/20 text-green-400 border-green-500/30"
                          : check.level === "warning"
                          ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
                          : "bg-red-500/20 text-red-400 border-red-500/30"
                      }`}
                    >
                      {check.level === "safe"
                        ? "PASS"
                        : check.level === "warning"
                        ? "WARN"
                        : "FAIL"}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <Progress
                    value={pct}
                    className="h-2"
                    indicatorClassName={
                      check.level === "safe"
                        ? "bg-green-500"
                        : check.level === "warning"
                        ? "bg-yellow-500"
                        : "bg-red-500"
                    }
                  />
                  <div className="text-xs text-muted-foreground">
                    {check.description}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Exposure Breakdown + Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Asset Exposure */}
          <Card className="bg-card/50 border-border/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Asset Exposure Breakdown
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {Object.keys(exposureByAsset).length === 0 ? (
                <div className="text-sm text-muted-foreground py-4 text-center">
                  No open positions
                </div>
              ) : (
                Object.entries(exposureByAsset)
                  .sort(([, a], [, b]) => b - a)
                  .map(([asset, value]) => {
                    const pct = totalValue > 0 ? (value / totalValue) * 100 : 0;
                    const overLimit = pct > MAX_SINGLE_EXPOSURE_PCT;
                    return (
                      <div key={asset}>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-white font-medium">{asset}</span>
                          <span
                            className={`font-mono ${
                              overLimit ? "text-red-400" : "text-muted-foreground"
                            }`}
                          >
                            {pct.toFixed(1)}%
                            {overLimit && (
                              <AlertTriangle className="inline h-3 w-3 ml-1" />
                            )}
                          </span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-background/50 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              overLimit ? "bg-red-500" : "bg-blue-500"
                            }`}
                            style={{ width: `${Math.min(pct, 100)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })
              )}
              <div className="flex justify-between text-xs text-muted-foreground pt-2">
                <span>Cash Reserve</span>
                <span className="font-mono">{availablePct.toFixed(1)}%</span>
              </div>
            </CardContent>
          </Card>

          {/* Trading Performance */}
          <Card className="bg-card/50 border-border/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Trading Performance
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-lg bg-background/50 p-3 text-center">
                  <div className="text-xs text-muted-foreground mb-1">
                    Win Rate
                  </div>
                  <div
                    className={`text-xl font-bold font-mono ${
                      winRate >= 50 ? "text-green-400" : winRate > 0 ? "text-red-400" : "text-white"
                    }`}
                  >
                    {winRate.toFixed(1)}%
                  </div>
                </div>
                <div className="rounded-lg bg-background/50 p-3 text-center">
                  <div className="text-xs text-muted-foreground mb-1">
                    Total Trades
                  </div>
                  <div className="text-xl font-bold font-mono text-white">
                    {state.closedTrades.length}
                  </div>
                </div>
                <div className="rounded-lg bg-background/50 p-3 text-center">
                  <div className="text-xs text-muted-foreground mb-1">
                    Drawdown
                  </div>
                  <div
                    className={`text-xl font-bold font-mono ${
                      drawdown > MAX_DRAWDOWN_PCT
                        ? "text-red-400"
                        : drawdown > 0
                        ? "text-yellow-400"
                        : "text-green-400"
                    }`}
                  >
                    {drawdown.toFixed(2)}%
                  </div>
                </div>
                <div className="rounded-lg bg-background/50 p-3 text-center">
                  <div className="text-xs text-muted-foreground mb-1">
                    Realized P&L
                  </div>
                  <div
                    className={`text-xl font-bold font-mono ${
                      state.realizedPnl >= 0 ? "text-green-400" : "text-red-400"
                    }`}
                  >
                    {state.realizedPnl >= 0 ? "+" : ""}$
                    {Math.abs(state.realizedPnl).toFixed(0)}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Position Size Calculator */}
        <PositionCalculator
          availableCapital={state.availableCapital}
          totalValue={totalValue}
          prices={prices}
        />

        {/* Correlation Matrix */}
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Grid3X3 className="h-4 w-4" />
              Asset Correlation Matrix
              <span className="text-[10px] text-muted-foreground ml-auto">
                Red = concentrated risk · Green = diversification benefit
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <CorrelationMatrix
              assets={DEFAULT_ASSETS.map((a) => a.symbol)}
              prices={prices}
            />
          </CardContent>
        </Card>
      </div>
    </>
  );
}
