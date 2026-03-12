// =============================================================================
// src/components/dashboard/regime-display.tsx — Market Regime Indicator
// =============================================================================

"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { MetricTooltip } from "@/components/ui/metric-tooltip";
import type { RegimeState } from "@/lib/types";
import { REGIME_COLORS, REGIME_LABELS } from "@/lib/types";

const REGIME_EXPLANATIONS: Record<RegimeState, string> = {
  RISK_ON: "Market conditions are favorable — high confidence signals, low uncertainty. Full signal generation active.",
  RISK_OFF: "Elevated caution — uncertainty rising or bearish indicators detected. Position sizes reduced.",
  CRISIS: "Extreme market stress detected — defensive mode. Only monitoring, no new signals.",
  TRANSITION: "Regime shift in progress — market moving between states. Signal reliability reduced.",
  UNKNOWN: "Insufficient data to determine regime. Waiting for backend connection.",
};

interface RegimeDisplayProps {
  regime: RegimeState;
  metaUncertainty: number;
  ece: number;
  oodScore: number;
  loading?: boolean;
}

export function RegimeDisplay({
  regime,
  metaUncertainty,
  ece,
  oodScore,
  loading,
}: RegimeDisplayProps) {
  const color = REGIME_COLORS[regime];
  const label = REGIME_LABELS[regime];

  // Determine meta-uncertainty state
  let uState = "NORMAL";
  let uColor = "#22c55e";
  if (metaUncertainty > 0.7) {
    uState = "COLLAPSE";
    uColor = "#ef4444";
  } else if (metaUncertainty > 0.5) {
    uState = "CONSERVATIVE";
    uColor = "#f97316";
  } else if (metaUncertainty > 0.3) {
    uState = "RECALIBRATION";
    uColor = "#eab308";
  }

  return (
    <Card className="bg-card/50 border-border/50">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          <MetricTooltip term="Market Regime">Market Regime</MetricTooltip>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Regime Badge */}
        {loading ? (
          <Skeleton className="h-8 w-28" />
        ) : (
          <div className="flex items-center gap-3">
            <div
              className="w-4 h-4 rounded-full animate-pulse"
              style={{ backgroundColor: color }}
            />
            <span className="text-2xl font-bold" style={{ color }}>
              {label}
            </span>
          </div>
        )}

        {/* Regime Explanation */}
        {!loading && (
          <p className="text-[11px] text-muted-foreground leading-relaxed">
            {REGIME_EXPLANATIONS[regime]}
          </p>
        )}

        {/* Metrics Grid */}
        <div className="grid grid-cols-3 gap-3">
          <MetricBox
            label="Meta-U"
            tooltipTerm="Meta-U"
            value={loading ? null : metaUncertainty.toFixed(3)}
            subLabel={loading ? null : uState}
            color={uColor}
          />
          <MetricBox
            label="ECE"
            tooltipTerm="ECE"
            value={loading ? null : ece.toFixed(4)}
            subLabel={loading ? null : ece < 0.05 ? "CALIBRATED" : "DRIFT"}
            color={ece < 0.05 ? "#22c55e" : "#ef4444"}
          />
          <MetricBox
            label="OOD"
            tooltipTerm="OOD"
            value={loading ? null : oodScore.toFixed(3)}
            subLabel={loading ? null : oodScore < 0.5 ? "IN-DIST" : "OOD"}
            color={oodScore < 0.5 ? "#22c55e" : "#ef4444"}
          />
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------

function MetricBox({
  label,
  tooltipTerm,
  value,
  subLabel,
  color,
}: {
  label: string;
  tooltipTerm: string;
  value: string | null;
  subLabel: string | null;
  color: string;
}) {
  return (
    <div className="rounded-lg bg-background/50 p-3 text-center">
      <div className="text-xs text-muted-foreground mb-1">
        <MetricTooltip term={tooltipTerm}>{label}</MetricTooltip>
      </div>
      {value === null ? (
        <Skeleton className="h-6 w-12 mx-auto" />
      ) : (
        <div className="text-lg font-mono font-bold text-white">{value}</div>
      )}
      {subLabel === null ? (
        <Skeleton className="h-4 w-16 mx-auto mt-1" />
      ) : (
        <Badge
          variant="outline"
          className="mt-1 text-[10px] px-1.5 py-0"
          style={{ borderColor: color, color }}
        >
          {subLabel}
        </Badge>
      )}
    </div>
  );
}
