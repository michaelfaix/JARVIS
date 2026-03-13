// =============================================================================
// src/app/(app)/radar/page.tsx — Opportunity Radar
// =============================================================================

"use client";

import { HudPanel } from "@/components/ui/hud-panel";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { useSignals } from "@/hooks/use-signals";
import { useSystemStatus } from "@/hooks/use-jarvis";
import { usePrices } from "@/hooks/use-prices";
import {
  REGIME_COLORS,
  REGIME_LABELS,
  type Opportunity,
  type RegimeState,
} from "@/lib/types";
import { DEFAULT_ASSETS, FREE_ASSETS } from "@/lib/constants";
import { useProfile } from "@/hooks/use-profile";
import { Radar, TrendingUp, TrendingDown } from "lucide-react";
import { ApiOfflineBanner } from "@/components/ui/api-offline-banner";

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
  const { regime, error: statusError } = useSystemStatus(5000);
  const { prices, priceHistory } = usePrices(5000);
  const { signals: allSignals, loading, error: signalsError } = useSignals(regime, 10000, prices, priceHistory);
  const { isPro } = useProfile();

  const signals = isPro
    ? allSignals
    : allSignals.filter((s) => FREE_ASSETS.includes(s.asset));

  const opportunities = deriveOpportunities(signals, regime);
  const topOpps = opportunities.slice(0, 6);
  const longs = opportunities.filter((o) => o.direction === "LONG");
  const shorts = opportunities.filter((o) => o.direction === "SHORT");

  return (
    <div className="p-2 sm:p-3 md:p-4 space-y-3">
      {(statusError || signalsError) && <ApiOfflineBanner />}
      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
          <div className="flex items-center gap-2 text-[10px] text-muted-foreground mb-1">
            <Radar className="h-3 w-3" /> OPPORTUNITIES
          </div>
          <div className="text-2xl font-bold font-mono text-white">
            {opportunities.length}
          </div>
        </div>
        <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
          <div className="flex items-center gap-2 text-[10px] text-muted-foreground mb-1">
            <TrendingUp className="h-3 w-3" /> LONG BIAS
          </div>
          <div className="text-2xl font-bold font-mono text-hud-green">
            {longs.length}
          </div>
        </div>
        <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
          <div className="flex items-center gap-2 text-[10px] text-muted-foreground mb-1">
            <TrendingDown className="h-3 w-3" /> SHORT BIAS
          </div>
          <div className="text-2xl font-bold font-mono text-hud-red">
            {shorts.length}
          </div>
        </div>
        <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
          <div className="text-[10px] text-muted-foreground mb-1">
            ACTIVE REGIME
          </div>
          <div
            className="text-xl font-bold font-mono"
            style={{ color: REGIME_COLORS[regime] }}
          >
            {REGIME_LABELS[regime]}
          </div>
        </div>
      </div>

      {/* Tabs: All / Long / Short */}
      <Tabs defaultValue="all">
        <TabsList className="bg-hud-bg/60 border border-hud-border/30">
          <TabsTrigger value="all" className="data-[state=active]:text-hud-cyan data-[state=active]:border-hud-cyan">All</TabsTrigger>
          <TabsTrigger value="long" className="data-[state=active]:text-hud-cyan data-[state=active]:border-hud-cyan">Long Only</TabsTrigger>
          <TabsTrigger value="short" className="data-[state=active]:text-hud-cyan data-[state=active]:border-hud-cyan">Short Only</TabsTrigger>
          <TabsTrigger value="top" className="data-[state=active]:text-hud-cyan data-[state=active]:border-hud-cyan">Top Picks</TabsTrigger>
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
      <HudPanel title="MOMENTUM SCANNER" scanLine>
        <div className="p-2.5">
          <div className="space-y-3">
            {opportunities.map((opp) => (
              <div
                key={opp.asset}
                className="flex items-center gap-4 py-2 border-b border-hud-border/30 last:border-0"
              >
                <div className="w-16 font-medium text-white text-sm font-mono">
                  {opp.asset}
                </div>
                <Badge
                  className={`text-[10px] w-14 justify-center ${
                    opp.direction === "LONG"
                      ? "bg-hud-green/20 text-hud-green border-hud-green/30"
                      : "bg-hud-red/20 text-hud-red border-hud-red/30"
                  }`}
                >
                  {opp.direction}
                </Badge>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-hud-bg/60 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          opp.momentum >= 0 ? "bg-hud-green" : "bg-hud-red"
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
                  <span className="text-xs font-mono text-hud-cyan">
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
        </div>
      </HudPanel>
    </div>
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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mt-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="bg-hud-bg/60 border border-hud-border/30 rounded animate-pulse h-40"
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
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mt-4">
      {opportunities.map((opp) => (
        <HudPanel key={opp.asset}>
          <div className="p-2.5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-bold text-white text-lg font-mono">
                  {opp.asset}
                </span>
                <Badge
                  className={
                    opp.direction === "LONG"
                      ? "bg-hud-green/20 text-hud-green border-hud-green/30"
                      : "bg-hud-red/20 text-hud-red border-hud-red/30"
                  }
                >
                  {opp.direction}
                </Badge>
              </div>
              <span className="text-2xl font-bold font-mono text-hud-cyan">
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
                <span className="text-[10px] text-muted-foreground">CONFIDENCE</span>
                <span className="font-mono text-white">
                  {(opp.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <Progress
                value={opp.confidence * 100}
                className="h-1.5"
                indicatorClassName={
                  opp.confidence > 0.7
                    ? "bg-hud-green"
                    : opp.confidence > 0.4
                    ? "bg-hud-amber"
                    : "bg-hud-red"
                }
              />
              <div className="flex justify-between text-xs">
                <span className="text-[10px] text-muted-foreground">QUALITY</span>
                <span className="font-mono text-white">
                  {(opp.qualityScore * 100).toFixed(0)}%
                </span>
              </div>
              <Progress
                value={opp.qualityScore * 100}
                className="h-1.5"
                indicatorClassName="bg-hud-cyan"
              />
            </div>
          </div>
        </HudPanel>
      ))}
    </div>
  );
}
