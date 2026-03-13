// =============================================================================
// src/app/(app)/risk/page.tsx — Risk Guardian
// =============================================================================

"use client";

import { useEffect } from "react";
import { HudPanel } from "@/components/ui/hud-panel";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { usePortfolio } from "@/hooks/use-portfolio";
import { useSystemStatus } from "@/hooks/use-jarvis";
import { usePrices } from "@/hooks/use-prices";
import { REGIME_COLORS } from "@/lib/types";
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
} from "lucide-react";
import { ApiOfflineBanner } from "@/components/ui/api-offline-banner";

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
  const { regime, error: statusError } = useSystemStatus(5000);
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
    safe: "text-hud-green",
    warning: "text-hud-amber",
    danger: "text-hud-red",
  };
  const levelBg = {
    safe: "bg-hud-green/10 border-hud-green/20",
    warning: "bg-hud-amber/10 border-hud-amber/20",
    danger: "bg-hud-red/10 border-hud-red/20",
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
      <div className="p-2 sm:p-3 md:p-4 space-y-3">
        {statusError && <ApiOfflineBanner />}
        {/* Overall Status */}
        <HudPanel>
          <div className={`p-3 rounded border ${levelBg[overallLevel]}`}>
            <div className="flex items-center gap-4">
              <LevelIcon className={`h-10 w-10 ${levelColors[overallLevel]}`} />
              <div>
                <div className={`text-2xl font-bold font-mono ${levelColors[overallLevel]}`}>
                  {levelLabels[overallLevel]}
                </div>
                <div className="text-[10px] text-hud-cyan/60 font-mono">
                  {dangerCount === 0 && warningCount === 0
                    ? "All risk checks passed. Portfolio is within safe parameters."
                    : `${dangerCount} critical, ${warningCount} warning${warningCount !== 1 ? "s" : ""}`}
                </div>
              </div>
              <div className="ml-auto flex items-center gap-3">
                <Badge
                  variant="outline"
                  className="text-[10px] font-mono"
                  style={{
                    borderColor: REGIME_COLORS[regime],
                    color: REGIME_COLORS[regime],
                  }}
                >
                  {regime.replace("_", " ")}
                </Badge>
              </div>
            </div>
          </div>
        </HudPanel>

        {/* Risk Score Gauge */}
        <RiskScoreGauge
          score={Math.min(100, Math.max(0, Math.round(
            (maxSingleExposurePct / MAX_SINGLE_EXPOSURE_PCT) * 25 +
            (drawdown / MAX_DRAWDOWN_PCT) * 25 +
            (state.positions.length / MAX_OPEN_POSITIONS) * 25 +
            (availablePct < 100 ? ((100 - availablePct) / (100 - MIN_AVAILABLE_CAPITAL_PCT)) * 25 : 0)
          ) || 0))}
          maxExposure={maxSingleExposurePct}
          openPositions={state.positions.length}
          drawdown={drawdown}
        />

        {/* Risk Checks Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {checks.map((check) => {
            const Icon = check.icon;
            const pct = Math.min((check.value / check.limit) * 100, 100);
            return (
              <HudPanel key={check.label}>
                <div className="p-2.5 space-y-2">
                  <div className="flex items-center gap-2">
                    <Icon className={`h-4 w-4 ${levelColors[check.level]}`} />
                    <span className="text-[10px] text-hud-cyan/70 font-mono uppercase">{check.label}</span>
                    <Badge
                      className={`ml-auto text-[10px] ${
                        check.level === "safe"
                          ? "bg-hud-green/15 text-hud-green border-hud-green/30"
                          : check.level === "warning"
                          ? "bg-hud-amber/15 text-hud-amber border-hud-amber/30"
                          : "bg-hud-red/15 text-hud-red border-hud-red/30"
                      }`}
                    >
                      {check.level === "safe"
                        ? "PASS"
                        : check.level === "warning"
                        ? "WARN"
                        : "FAIL"}
                    </Badge>
                  </div>
                  <Progress
                    value={pct}
                    className="h-2"
                    indicatorClassName={
                      check.level === "safe"
                        ? "bg-hud-green"
                        : check.level === "warning"
                        ? "bg-hud-amber"
                        : "bg-hud-red"
                    }
                  />
                  <div className="text-[10px] text-hud-cyan/50 font-mono">
                    {check.description}
                  </div>
                </div>
              </HudPanel>
            );
          })}
        </div>

        {/* Exposure Breakdown + Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          {/* Asset Exposure */}
          <HudPanel title="ASSET EXPOSURE">
            <div className="p-2.5 space-y-3">
              {Object.keys(exposureByAsset).length === 0 ? (
                <div className="text-[10px] text-hud-cyan/50 font-mono py-4 text-center">
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
                          <span className="text-hud-cyan font-medium font-mono">{asset}</span>
                          <span
                            className={`font-mono ${
                              overLimit ? "text-hud-red" : "text-hud-cyan/60"
                            }`}
                          >
                            {pct.toFixed(1)}%
                            {overLimit && (
                              <AlertTriangle className="inline h-3 w-3 ml-1" />
                            )}
                          </span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-hud-bg/60 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              overLimit ? "bg-hud-red" : "bg-hud-cyan"
                            }`}
                            style={{ width: `${Math.min(pct, 100)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })
              )}
              <div className="flex justify-between text-[10px] text-hud-cyan/50 font-mono pt-2">
                <span>Cash Reserve</span>
                <span>{availablePct.toFixed(1)}%</span>
              </div>
            </div>
          </HudPanel>

          {/* Trading Performance */}
          <HudPanel title="TRADING PERFORMANCE">
            <div className="p-2.5">
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5 text-center">
                  <div className="text-[10px] text-hud-cyan/60 font-mono mb-1">
                    WIN RATE
                  </div>
                  <div
                    className={`text-xl font-bold font-mono ${
                      winRate >= 50 ? "text-hud-green" : winRate > 0 ? "text-hud-red" : "text-hud-cyan"
                    }`}
                  >
                    {winRate.toFixed(1)}%
                  </div>
                </div>
                <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5 text-center">
                  <div className="text-[10px] text-hud-cyan/60 font-mono mb-1">
                    TOTAL TRADES
                  </div>
                  <div className="text-xl font-bold font-mono text-hud-cyan">
                    {state.closedTrades.length}
                  </div>
                </div>
                <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5 text-center">
                  <div className="text-[10px] text-hud-cyan/60 font-mono mb-1">
                    DRAWDOWN
                  </div>
                  <div
                    className={`text-xl font-bold font-mono ${
                      drawdown > MAX_DRAWDOWN_PCT
                        ? "text-hud-red"
                        : drawdown > 0
                        ? "text-hud-amber"
                        : "text-hud-green"
                    }`}
                  >
                    {drawdown.toFixed(2)}%
                  </div>
                </div>
                <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5 text-center">
                  <div className="text-[10px] text-hud-cyan/60 font-mono mb-1">
                    REALIZED P&L
                  </div>
                  <div
                    className={`text-xl font-bold font-mono ${
                      state.realizedPnl >= 0 ? "text-hud-green" : "text-hud-red"
                    }`}
                  >
                    {state.realizedPnl >= 0 ? "+" : ""}$
                    {Math.abs(state.realizedPnl).toFixed(0)}
                  </div>
                </div>
              </div>
            </div>
          </HudPanel>
        </div>

        {/* Position Size Calculator */}
        <PositionCalculator
          availableCapital={state.availableCapital}
          totalValue={totalValue}
          prices={prices}
        />

        {/* Correlation Matrix */}
        <HudPanel title="ASSET CORRELATION MATRIX">
          <div className="p-2.5">
            <div className="flex items-center justify-end mb-2">
              <span className="text-[9px] text-hud-cyan/40 font-mono">
                Red = concentrated risk · Green = diversification benefit
              </span>
            </div>
            <CorrelationMatrix
              assets={DEFAULT_ASSETS.map((a) => a.symbol)}
              prices={prices}
            />
          </div>
        </HudPanel>
      </div>
    </>
  );
}
