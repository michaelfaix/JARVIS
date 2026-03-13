// =============================================================================
// src/components/dashboard/regime-display.tsx — Market Regime (HUD)
// =============================================================================

"use client";

import React from "react";
import { HudPanel } from "@/components/ui/hud-panel";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { MetricTooltip } from "@/components/ui/metric-tooltip";
import type { RegimeState } from "@/lib/types";
import { REGIME_COLORS, REGIME_LABELS } from "@/lib/types";

const REGIME_EXPLANATIONS: Record<RegimeState, string> = {
  RISK_ON: "Favorable conditions — full signal generation active.",
  RISK_OFF: "Elevated caution — position sizes reduced.",
  CRISIS: "Extreme stress — defensive mode, monitoring only.",
  TRANSITION: "Regime shift in progress — reliability reduced.",
  UNKNOWN: "Insufficient data — awaiting backend.",
};

interface RegimeDisplayProps {
  regime: RegimeState;
  metaUncertainty: number;
  ece: number;
  oodScore: number;
  loading?: boolean;
}

export const RegimeDisplay = React.memo(function RegimeDisplay({ regime, metaUncertainty, ece, oodScore, loading }: RegimeDisplayProps) {
  const color = REGIME_COLORS[regime];
  const label = REGIME_LABELS[regime];

  let uState = "NORMAL";
  let uColor = "#00e5a0";
  if (metaUncertainty > 0.7) { uState = "COLLAPSE"; uColor = "#ff4466"; }
  else if (metaUncertainty > 0.5) { uState = "CONSERVATIVE"; uColor = "#ffaa00"; }
  else if (metaUncertainty > 0.3) { uState = "RECALIBRATION"; uColor = "#ffaa00"; }

  return (
    <HudPanel title="Market Regime">
      <div className="p-2.5 space-y-2">
        {loading ? (
          <Skeleton className="h-7 w-24" />
        ) : (
          <div className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full animate-pulse-live"
              style={{ backgroundColor: color }}
            />
            <span className="text-lg font-bold font-mono" style={{ color }}>{label}</span>
          </div>
        )}

        {!loading && (
          <p className="text-[9px] font-mono text-muted-foreground/60 leading-relaxed">
            {REGIME_EXPLANATIONS[regime]}
          </p>
        )}

        <div className="grid grid-cols-3 gap-1.5">
          <MetricBox label="Meta-U" tooltipTerm="Meta-U" value={loading ? null : metaUncertainty.toFixed(3)} subLabel={loading ? null : uState} color={uColor} />
          <MetricBox label="ECE" tooltipTerm="ECE" value={loading ? null : ece.toFixed(4)} subLabel={loading ? null : ece < 0.05 ? "CALIBRATED" : "DRIFT"} color={ece < 0.05 ? "#00e5a0" : "#ff4466"} />
          <MetricBox label="OOD" tooltipTerm="OOD" value={loading ? null : oodScore.toFixed(3)} subLabel={loading ? null : oodScore < 0.5 ? "IN-DIST" : "OOD"} color={oodScore < 0.5 ? "#00e5a0" : "#ff4466"} />
        </div>
      </div>
    </HudPanel>
  );
});

function MetricBox({ label, tooltipTerm, value, subLabel, color }: { label: string; tooltipTerm: string; value: string | null; subLabel: string | null; color: string }) {
  return (
    <div className="rounded bg-hud-bg/60 border border-hud-border/30 p-2 text-center">
      <div className="text-[8px] font-mono text-muted-foreground/60 mb-0.5">
        <MetricTooltip term={tooltipTerm}>{label}</MetricTooltip>
      </div>
      {value === null ? (
        <Skeleton className="h-5 w-10 mx-auto" />
      ) : (
        <div className="text-sm font-mono font-bold text-white">{value}</div>
      )}
      {subLabel === null ? (
        <Skeleton className="h-3 w-12 mx-auto mt-0.5" />
      ) : (
        <Badge variant="outline" className="mt-0.5 text-[8px] px-1 py-0 font-mono" style={{ borderColor: color, color }}>
          {subLabel}
        </Badge>
      )}
    </div>
  );
}
