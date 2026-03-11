// =============================================================================
// src/app/(app)/radar/page.tsx — Opportunity Radar
// =============================================================================

"use client";

import { AppHeader } from "@/components/layout/app-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { useSignals } from "@/hooks/use-signals";
import { useSystemStatus } from "@/hooks/use-jarvis";
import {
  inferRegime,
  REGIME_COLORS,
  REGIME_LABELS,
  type Opportunity,
  type RegimeState,
} from "@/lib/types";
import { DEFAULT_ASSETS } from "@/lib/constants";
import { Radar, TrendingUp, TrendingDown, Zap } from "lucide-react";

// Derive opportunities from signals
function deriveOpportunities(
  signals: ReturnType<typeof useSignals>["signals"],
  regime: RegimeState
): Opportunity[] {
  return signals
    .map((s) => {
      const asset = DEFAULT_ASSETS.find((a) => a.symbol === s.asset);
      // Momentum = normalized direction strength
      const momentum = s.direction === "LONG" ? s.confidence : -s.confidence;
      const score = s.confidence * s.qualityScore;
      return {
        asset: s.asset,
        direction: s.direction,
        score,
        confidence: s.confidence,
        momentum,
        regime,
        qualityScore: s.qualityScore,
        price: asset?.price ?? s.entry,
      };
    })
    .sort((a, b) => b.score - a.score);
}

export default function RadarPage() {
  const { status } = useSystemStatus(5000);
  const regime: RegimeState = status ? inferRegime(status.modus) : "RISK_ON";
  const { signals, loading } = useSignals(regime, 10000);

  const opportunities = deriveOpportunities(signals, regime);
  const topOpps = opportunities.slice(0, 6);
  const longs = opportunities.filter((o) => o.direction === "LONG");
  const shorts = opportunities.filter((o) => o.direction === "SHORT");

  return (
    <>
      <AppHeader title="Opportunity Radar" subtitle="Regime + Momentum Scanner" />
      <div className="p-6 space-y-6">
        {/* Summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                <Radar className="h-3 w-3" /> Opportunities
              </div>
              <div className="text-2xl font-bold font-mono text-white">
                {opportunities.length}
              </div>
            </CardContent>
          </Card>
          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                <TrendingUp className="h-3 w-3" /> Long Bias
              </div>
              <div className="text-2xl font-bold font-mono text-green-400">
                {longs.length}
              </div>
            </CardContent>
          </Card>
          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                <TrendingDown className="h-3 w-3" /> Short Bias
              </div>
              <div className="text-2xl font-bold font-mono text-red-400">
                {shorts.length}
              </div>
            </CardContent>
          </Card>
          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="text-xs text-muted-foreground mb-1">
                Active Regime
              </div>
              <div
                className="text-xl font-bold"
                style={{ color: REGIME_COLORS[regime] }}
              >
                {REGIME_LABELS[regime]}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs: All / Long / Short */}
        <Tabs defaultValue="all">
          <TabsList>
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="long">Long Only</TabsTrigger>
            <TabsTrigger value="short">Short Only</TabsTrigger>
            <TabsTrigger value="top">Top Picks</TabsTrigger>
          </TabsList>

          <TabsContent value="all">
            <OpportunityGrid
              opportunities={opportunities}
              loading={loading}
            />
          </TabsContent>
          <TabsContent value="long">
            <OpportunityGrid
              opportunities={longs}
              loading={loading}
            />
          </TabsContent>
          <TabsContent value="short">
            <OpportunityGrid
              opportunities={shorts}
              loading={loading}
            />
          </TabsContent>
          <TabsContent value="top">
            <OpportunityGrid
              opportunities={topOpps}
              loading={loading}
            />
          </TabsContent>
        </Tabs>

        {/* Momentum Scanner */}
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Momentum Scanner
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {opportunities.map((opp) => (
                <div
                  key={opp.asset}
                  className="flex items-center gap-4 py-2 border-b border-border/30 last:border-0"
                >
                  <div className="w-16 font-medium text-white text-sm">
                    {opp.asset}
                  </div>
                  <Badge
                    className={`text-[10px] w-14 justify-center ${
                      opp.direction === "LONG"
                        ? "bg-green-500/20 text-green-400 border-green-500/30"
                        : "bg-red-500/20 text-red-400 border-red-500/30"
                    }`}
                  >
                    {opp.direction}
                  </Badge>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-2 bg-background/50 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            opp.momentum >= 0 ? "bg-green-500" : "bg-red-500"
                          }`}
                          style={{
                            width: `${Math.abs(opp.momentum) * 100}%`,
                            marginLeft:
                              opp.momentum < 0
                                ? `${(1 - Math.abs(opp.momentum)) * 50}%`
                                : "50%",
                          }}
                        />
                      </div>
                      <span className="text-xs font-mono text-muted-foreground w-12 text-right">
                        {opp.momentum >= 0 ? "+" : ""}
                        {(opp.momentum * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="text-right w-20">
                    <span className="text-xs font-mono text-white">
                      Score: {(opp.score * 100).toFixed(0)}
                    </span>
                  </div>
                </div>
              ))}
              {opportunities.length === 0 && (
                <div className="text-center text-muted-foreground py-6 text-sm">
                  {loading
                    ? "Scanning markets..."
                    : "Connect backend to scan opportunities"}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// OpportunityGrid
// ---------------------------------------------------------------------------

function OpportunityGrid({
  opportunities,
  loading,
}: {
  opportunities: Opportunity[];
  loading: boolean;
}) {
  if (loading && opportunities.length === 0) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <Card
            key={i}
            className="bg-card/50 border-border/50 animate-pulse h-40"
          />
        ))}
      </div>
    );
  }

  if (opportunities.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-12 text-sm">
        No opportunities found for current filters
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
      {opportunities.map((opp) => (
        <Card key={opp.asset} className="bg-card/50 border-border/50">
          <CardContent className="pt-4 pb-3 px-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-bold text-white text-lg">
                  {opp.asset}
                </span>
                <Badge
                  className={
                    opp.direction === "LONG"
                      ? "bg-green-500/20 text-green-400 border-green-500/30"
                      : "bg-red-500/20 text-red-400 border-red-500/30"
                  }
                >
                  {opp.direction}
                </Badge>
              </div>
              <span className="text-2xl font-bold font-mono text-white">
                {(opp.score * 100).toFixed(0)}
              </span>
            </div>

            <div className="text-sm font-mono text-muted-foreground">
              $
              {opp.price.toLocaleString("en-US", {
                minimumFractionDigits: 2,
              })}
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">Confidence</span>
                <span className="font-mono text-white">
                  {(opp.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <Progress
                value={opp.confidence * 100}
                className="h-1.5"
                indicatorClassName={
                  opp.confidence > 0.7
                    ? "bg-green-500"
                    : opp.confidence > 0.4
                    ? "bg-yellow-500"
                    : "bg-red-500"
                }
              />
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">Quality</span>
                <span className="font-mono text-white">
                  {(opp.qualityScore * 100).toFixed(0)}%
                </span>
              </div>
              <Progress
                value={opp.qualityScore * 100}
                className="h-1.5"
                indicatorClassName="bg-blue-500"
              />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
