// =============================================================================
// src/components/dashboard/regime-display.tsx — Market Regime Indicator
// =============================================================================

"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { RegimeState } from "@/lib/types";
import { REGIME_COLORS, REGIME_LABELS } from "@/lib/types";

interface RegimeDisplayProps {
  regime: RegimeState;
  metaUncertainty: number;
  ece: number;
  oodScore: number;
}

export function RegimeDisplay({
  regime,
  metaUncertainty,
  ece,
  oodScore,
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
          Market Regime
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Regime Badge */}
        <div className="flex items-center gap-3">
          <div
            className="w-4 h-4 rounded-full animate-pulse"
            style={{ backgroundColor: color }}
          />
          <span className="text-2xl font-bold" style={{ color }}>
            {label}
          </span>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-3 gap-3">
          <MetricBox
            label="Meta-U"
            value={metaUncertainty.toFixed(3)}
            subLabel={uState}
            color={uColor}
          />
          <MetricBox
            label="ECE"
            value={ece.toFixed(4)}
            subLabel={ece < 0.05 ? "CALIBRATED" : "DRIFT"}
            color={ece < 0.05 ? "#22c55e" : "#ef4444"}
          />
          <MetricBox
            label="OOD"
            value={oodScore.toFixed(3)}
            subLabel={oodScore < 0.5 ? "IN-DIST" : "OOD"}
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
  value,
  subLabel,
  color,
}: {
  label: string;
  value: string;
  subLabel: string;
  color: string;
}) {
  return (
    <div className="rounded-lg bg-background/50 p-3 text-center">
      <div className="text-xs text-muted-foreground mb-1">{label}</div>
      <div className="text-lg font-mono font-bold text-white">{value}</div>
      <Badge
        variant="outline"
        className="mt-1 text-[10px] px-1.5 py-0"
        style={{ borderColor: color, color }}
      >
        {subLabel}
      </Badge>
    </div>
  );
}
