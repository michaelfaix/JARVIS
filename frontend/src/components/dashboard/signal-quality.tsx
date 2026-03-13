// =============================================================================
// src/components/dashboard/signal-quality.tsx — Signal Quality (HUD)
// =============================================================================

"use client";

import { useMemo } from "react";
import { HudPanel } from "@/components/ui/hud-panel";
import { Progress } from "@/components/ui/progress";
import type { Signal } from "@/lib/types";
import type { MetricsResponse } from "@/lib/api";
import { AlertTriangle, Brain, Target } from "lucide-react";

interface SignalQualityProps {
  signals: Signal[];
  metrics: MetricsResponse | null;
  accuracyByAsset: {
    asset: string;
    totalTrades: number;
    wins: number;
    losses: number;
    winRate: number;
    avgPnlPercent: number;
  }[];
  backendOnline: boolean;
}

function UncertaintyBar({ label, value, max, color }: { label: string; value: number; max: number; color: string }) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-[9px] font-mono text-muted-foreground w-14 shrink-0">{label}</span>
      <div className="flex-1 h-1 rounded-full bg-hud-bg overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[9px] font-mono text-muted-foreground w-8 text-right">{(value * 100).toFixed(0)}%</span>
    </div>
  );
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function SignalQuality({ signals, metrics, accuracyByAsset, backendOnline }: SignalQualityProps) {
  const stats = useMemo(() => {
    if (signals.length === 0) return null;

    const avgConfidence = signals.reduce((s, sig) => s + sig.confidence, 0) / signals.length;
    const avgQuality = signals.reduce((s, sig) => s + sig.qualityScore, 0) / signals.length;
    const oodCount = signals.filter((s) => s.isOod).length;
    const deepPathCount = signals.filter((s) => s.deepPathUsed).length;

    const withUncertainty = signals.filter((s) => s.uncertainty);
    const avgUncertainty =
      withUncertainty.length > 0
        ? {
            aleatoric: withUncertainty.reduce((s, sig) => s + (sig.uncertainty?.aleatoric ?? 0), 0) / withUncertainty.length,
            epistemic_model: withUncertainty.reduce((s, sig) => s + (sig.uncertainty?.epistemic_model ?? 0), 0) / withUncertainty.length,
            epistemic_data: withUncertainty.reduce((s, sig) => s + (sig.uncertainty?.epistemic_data ?? 0), 0) / withUncertainty.length,
            total: withUncertainty.reduce((s, sig) => s + (sig.uncertainty?.total ?? 0), 0) / withUncertainty.length,
          }
        : null;

    return { avgConfidence, avgQuality, oodCount, deepPathCount, avgUncertainty, totalSignals: signals.length };
  }, [signals]);

  if (!stats) {
    return (
      <HudPanel title="Signal Quality">
        <div className="p-3 text-[10px] text-muted-foreground text-center py-6 font-mono">
          No signals available
        </div>
      </HudPanel>
    );
  }

  return (
    <HudPanel title="Signal Quality" scanLine>
      <div className="p-2.5 space-y-2.5">
        {/* Confidence & Quality */}
        <div className="grid grid-cols-2 gap-2">
          <div className="rounded bg-hud-bg/60 border border-hud-border/30 p-2">
            <div className="text-[9px] font-mono text-muted-foreground mb-0.5 flex items-center gap-1">
              <Target className="h-2.5 w-2.5" /> Avg Conf
            </div>
            <div className="text-sm font-mono font-bold text-white">{(stats.avgConfidence * 100).toFixed(0)}%</div>
            <Progress value={stats.avgConfidence * 100} className="h-1 mt-1" indicatorClassName={stats.avgConfidence > 0.7 ? "bg-hud-green" : stats.avgConfidence > 0.4 ? "bg-hud-amber" : "bg-hud-red"} />
          </div>
          <div className="rounded bg-hud-bg/60 border border-hud-border/30 p-2">
            <div className="text-[9px] font-mono text-muted-foreground mb-0.5 flex items-center gap-1">
              <Brain className="h-2.5 w-2.5" /> Avg Qual
            </div>
            <div className="text-sm font-mono font-bold text-white">{(stats.avgQuality * 100).toFixed(0)}%</div>
            <Progress value={stats.avgQuality * 100} className="h-1 mt-1" indicatorClassName={stats.avgQuality > 0.7 ? "bg-hud-green" : stats.avgQuality > 0.4 ? "bg-hud-amber" : "bg-hud-red"} />
          </div>
        </div>

        {/* OOD + Deep Path */}
        {(stats.oodCount > 0 || stats.deepPathCount > 0) && (
          <div className="flex flex-wrap gap-2">
            {stats.oodCount > 0 && (
              <div className="flex items-center gap-1 text-[9px] font-mono text-hud-amber">
                <AlertTriangle className="h-2.5 w-2.5" /> {stats.oodCount}/{stats.totalSignals} OOD
              </div>
            )}
            {stats.deepPathCount > 0 && (
              <div className="flex items-center gap-1 text-[9px] font-mono text-hud-cyan">
                <Brain className="h-2.5 w-2.5" /> {stats.deepPathCount} Deep Path
              </div>
            )}
          </div>
        )}

        {/* Uncertainty Decomposition */}
        {stats.avgUncertainty && (
          <div className="space-y-1">
            <div className="text-[9px] font-mono text-muted-foreground/60 uppercase tracking-wider">Uncertainty</div>
            <UncertaintyBar label="Aleatoric" value={stats.avgUncertainty.aleatoric} max={0.5} color="bg-hud-cyan" />
            <UncertaintyBar label="Epistemic" value={stats.avgUncertainty.epistemic_model} max={0.5} color="bg-purple-500" />
            <UncertaintyBar label="Data" value={stats.avgUncertainty.epistemic_data} max={0.5} color="bg-hud-amber" />
          </div>
        )}

        {/* Calibration metrics */}
        {metrics && (
          <div className="grid grid-cols-3 gap-1.5">
            {[
              { label: "Cal.", value: metrics.calibration_component },
              { label: "Stab.", value: metrics.stability_component },
              { label: "Data", value: metrics.data_quality_component },
            ].map((m) => (
              <div key={m.label} className="text-center">
                <div className="text-[8px] font-mono text-muted-foreground/60">{m.label}</div>
                <div className={`text-[10px] font-mono font-bold ${m.value > 0.8 ? "text-hud-green" : m.value > 0.5 ? "text-hud-amber" : "text-hud-red"}`}>
                  {(m.value * 100).toFixed(0)}%
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Per-asset accuracy */}
        {accuracyByAsset.length > 0 && (
          <div className="space-y-1">
            <div className="text-[9px] font-mono text-muted-foreground/60 uppercase tracking-wider">Accuracy</div>
            {accuracyByAsset.map((acc) => (
              <div key={acc.asset} className="flex items-center gap-1.5 text-[9px]">
                <span className="font-mono font-medium text-white w-8">{acc.asset}</span>
                <div className="flex-1 h-1 rounded-full bg-hud-bg overflow-hidden">
                  <div className={`h-full rounded-full ${acc.winRate >= 60 ? "bg-hud-green" : acc.winRate >= 40 ? "bg-hud-amber" : "bg-hud-red"}`} style={{ width: `${acc.winRate}%` }} />
                </div>
                <span className="font-mono text-muted-foreground w-12 text-right">{acc.winRate.toFixed(0)}%</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </HudPanel>
  );
}
