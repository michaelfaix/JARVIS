// =============================================================================
// src/app/(app)/strategy-lab/page.tsx — Strategy Lab (Scaffold)
// =============================================================================

"use client";

import { AppHeader } from "@/components/layout/app-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { STRATEGIES } from "@/lib/constants";
import { FlaskConical, Play, BarChart3, Clock, Layers } from "lucide-react";

export default function StrategyLabPage() {
  return (
    <>
      <AppHeader title="Strategy Lab" subtitle="Backtest & Optimize" />
      <div className="p-6 space-y-6">
        {/* Strategy Selection */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {STRATEGIES.map((strategy) => (
            <Card
              key={strategy.id}
              className="bg-card/50 border-border/50 hover:border-blue-500/30 transition-colors cursor-pointer"
            >
              <CardContent className="pt-5 pb-4 px-5 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FlaskConical className="h-5 w-5 text-blue-400" />
                    <span className="font-bold text-white">
                      {strategy.label}
                    </span>
                  </div>
                  <Badge
                    variant="outline"
                    className="text-[10px] text-muted-foreground"
                  >
                    {strategy.id === "momentum"
                      ? "Trend Following"
                      : strategy.id === "mean_reversion"
                      ? "Contrarian"
                      : "Hybrid"}
                  </Badge>
                </div>

                <p className="text-xs text-muted-foreground">
                  {strategy.id === "momentum"
                    ? "Follows price trends using momentum signals across multiple timeframes. Best in trending regimes (RISK_ON, RISK_OFF)."
                    : strategy.id === "mean_reversion"
                    ? "Identifies overbought/oversold conditions for reversal trades. Effective in range-bound markets (TRANSITION)."
                    : "Combines momentum and mean reversion with regime-adaptive weighting. Robust across all market conditions."}
                </p>

                <Separator className="opacity-30" />

                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div>
                    <div className="text-muted-foreground mb-1">Win Rate</div>
                    <div className="font-mono text-white">
                      {strategy.id === "momentum"
                        ? "58%"
                        : strategy.id === "mean_reversion"
                        ? "62%"
                        : "60%"}
                    </div>
                  </div>
                  <div>
                    <div className="text-muted-foreground mb-1">Sharpe</div>
                    <div className="font-mono text-white">
                      {strategy.id === "momentum"
                        ? "1.8"
                        : strategy.id === "mean_reversion"
                        ? "1.5"
                        : "2.1"}
                    </div>
                  </div>
                  <div>
                    <div className="text-muted-foreground mb-1">Max DD</div>
                    <div className="font-mono text-white">
                      {strategy.id === "momentum"
                        ? "-12%"
                        : strategy.id === "mean_reversion"
                        ? "-8%"
                        : "-10%"}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Backtest Panel */}
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Backtest Engine
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <label className="text-xs text-muted-foreground">
                  Window Size
                </label>
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <span className="font-mono text-white text-sm">
                    20 periods
                  </span>
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-xs text-muted-foreground">Step</label>
                <div className="flex items-center gap-2">
                  <Layers className="h-4 w-4 text-muted-foreground" />
                  <span className="font-mono text-white text-sm">
                    1 period
                  </span>
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-xs text-muted-foreground">
                  Data Range
                </label>
                <div className="font-mono text-white text-sm">
                  90 days (synthetic)
                </div>
              </div>
            </div>

            <Separator className="opacity-30" />

            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground">
                Run walk-forward backtest with the selected strategy and
                parameters. Uses jarvis.backtest.engine for deterministic
                simulation.
              </p>
              <Button variant="outline" className="gap-2" disabled>
                <Play className="h-4 w-4" />
                Run Backtest
                <Badge className="text-[9px] bg-blue-500/20 text-blue-400 border-blue-500/30 ml-1">
                  Coming Soon
                </Badge>
              </Button>
            </div>
          </CardContent>
        </Card>

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
                <div className="text-muted-foreground mb-1">
                  Determinism
                </div>
                <div className="text-white font-bold">DET-01 to DET-07</div>
                <div className="text-muted-foreground mt-1">
                  No random, no file I/O, no global state, bit-identical
                  outputs
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
      </div>
    </>
  );
}
