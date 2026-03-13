// =============================================================================
// src/components/dashboard/system-status.tsx — System Status Widget (Iron Man HUD)
// =============================================================================

"use client";

import React from "react";
import { HudPanel } from "@/components/ui/hud-panel";
import { Skeleton } from "@/components/ui/skeleton";
import { MetricTooltip } from "@/components/ui/metric-tooltip";
import { MODUS_COLORS } from "@/lib/types";
import type { MetricsResponse } from "@/lib/api";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const MODUS_SEVERITY: Record<string, number> = {
  NORMAL: 0, ERHOEHTE_VORSICHT: 1, REDUZIERTES_VERTRAUEN: 2,
  MINIMALE_EXPOSITION: 3, NUR_MONITORING: 4, NOTFALL_MODUS: 5,
  DATEN_QUARANTAENE: 6, MODELL_ROLLBACK: 7, KONFIDENZ_KOLLAPS: 8,
};

const MODUS_LABELS: Record<string, string> = {
  NORMAL: "NORMAL", ERHOEHTE_VORSICHT: "VORSICHT", REDUZIERTES_VERTRAUEN: "RED. VERTRAUEN",
  MINIMALE_EXPOSITION: "MIN. EXPOSITION", NUR_MONITORING: "MONITORING",
  NOTFALL_MODUS: "NOTFALL", DATEN_QUARANTAENE: "QUARANTÄNE",
  MODELL_ROLLBACK: "ROLLBACK", KONFIDENZ_KOLLAPS: "KOLLAPS",
};

function barColor(v: number): string {
  if (v >= 0.8) return "#00e5a0";
  if (v >= 0.5) return "#ffaa00";
  return "#ff4466";
}

function HudLabel({ children }: { children: React.ReactNode }) {
  return <span className="font-mono text-[7px] tracking-[2px] text-[#2a3a52] uppercase">{children}</span>;
}

function ThinBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="w-full h-[2px] bg-[#0a1528] rounded-full overflow-hidden">
      <div className="h-full rounded-full transition-all duration-500" style={{ width: `${Math.min(100, value)}%`, backgroundColor: color }} />
    </div>
  );
}

// ---------------------------------------------------------------------------
// System Mode Card — SECTION 1 + 4 + 5
// ---------------------------------------------------------------------------

interface SystemModeCardProps {
  modus: string;
  vorhersagenAktiv: boolean;
  konfidenzMultiplikator: number;
  entscheidungsCount: number;
  ece: number;
  oodScore: number;
  metaUncertainty: number;
  loading?: boolean;
  backendOnline?: boolean;
}

export const SystemModeCard = React.memo(function SystemModeCard({
  modus, vorhersagenAktiv, konfidenzMultiplikator, entscheidungsCount,
  ece, oodScore, metaUncertainty, loading, backendOnline = false,
}: SystemModeCardProps) {
  const color = MODUS_COLORS[modus] || "#6b7280";
  const label = MODUS_LABELS[modus] || modus.replace(/_/g, " ");
  const severity = MODUS_SEVERITY[modus] ?? 0;

  return (
    <HudPanel>
      <div className="p-2 space-y-2.5">
        {loading ? (
          <div className="space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-[2px] w-full" />
            {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-3 w-full" />)}
          </div>
        ) : (
          <>
            {/* SECTION 1: Status Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <HudLabel>SYSTEM STATUS</HudLabel>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full animate-pulse-live" style={{ backgroundColor: color, boxShadow: `0 0 6px ${color}` }} />
                <span className="font-mono text-[10px] font-bold" style={{ color }}>
                  {backendOnline ? (modus === "NORMAL" ? "RISK ON" : label) : "OFFLINE"}
                </span>
              </div>
              <span className="font-mono text-[8px] text-muted-foreground">{label}</span>
            </div>

            <div className="border-t border-hud-border/20" />

            {/* SECTION 4: ML Metrics */}
            <div>
              <HudLabel>ML METRIKEN</HudLabel>
              <div className="mt-1.5 space-y-1.5">
                <div className="flex items-center justify-between">
                  <MetricTooltip term="ECE"><span className="font-mono text-[8px] text-muted-foreground">ECE CALIBRATION</span></MetricTooltip>
                  <span className={`font-mono text-[10px] font-bold ${ece > 0.08 ? "text-hud-amber" : "text-hud-green"}`}>
                    {ece.toFixed(4)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <MetricTooltip term="OOD Score"><span className="font-mono text-[8px] text-muted-foreground">OOD SCORE</span></MetricTooltip>
                  <div className="flex items-center gap-1.5">
                    <span className={`font-mono text-[10px] font-bold ${oodScore > 0.5 ? "text-hud-red" : oodScore > 0.3 ? "text-hud-amber" : "text-hud-green"}`}>
                      {oodScore.toFixed(3)}
                    </span>
                    <span className={`font-mono text-[7px] ${oodScore < 0.5 ? "text-hud-green" : "text-hud-red"}`}>
                      {oodScore < 0.5 ? "IN-DIST" : "OOD"}
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <MetricTooltip term="Meta Uncertainty"><span className="font-mono text-[8px] text-muted-foreground">META-U</span></MetricTooltip>
                  <div className="flex items-center gap-1.5">
                    <span className="font-mono text-[10px] font-bold text-white">
                      {metaUncertainty.toFixed(3)}
                    </span>
                    <span className="font-mono text-[7px] text-muted-foreground">
                      {metaUncertainty < 0.1 ? "NORMAL" : metaUncertainty < 0.3 ? "ELEVATED" : "HIGH"}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="border-t border-hud-border/20" />

            {/* SECTION 5: System Info */}
            <div>
              <HudLabel>SYSTEM INFO</HudLabel>
              <div className="mt-1.5 space-y-1">
                <InfoRow label="SEVERITY" value={`${severity} / 8`} />
                <InfoRow label="CONF. MULT." value={`${konfidenzMultiplikator.toFixed(2)}×`} color={konfidenzMultiplikator < 0.95 ? "#ffaa00" : undefined} />
                <InfoRow label="DECISIONS" value={entscheidungsCount.toLocaleString()} />
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[8px] text-muted-foreground">PREDICTIONS</span>
                  <span className={`font-mono text-[9px] font-bold ${vorhersagenAktiv ? "text-hud-green" : "text-hud-red"}`}>
                    {vorhersagenAktiv ? "ACTIVE" : "OFF"}
                  </span>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </HudPanel>
  );
});

function InfoRow({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="font-mono text-[8px] text-muted-foreground">{label}</span>
      <span className="font-mono text-[10px] font-bold" style={color ? { color } : undefined}>
        {value}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Quality Score Card — SECTION 2 + 3
// ---------------------------------------------------------------------------

interface QualityScoreCardProps {
  metrics: MetricsResponse | null;
  loading?: boolean;
}

export const QualityScoreCard = React.memo(function QualityScoreCard({ metrics, loading }: QualityScoreCardProps) {
  if (!metrics || loading) {
    return (
      <HudPanel>
        <div className="p-2 space-y-2">
          <HudLabel>DECISION QUALITY</HudLabel>
          <Skeleton className="h-7 w-20" />
          <Skeleton className="h-[2px] w-full" />
          {[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-3 w-full" />)}
        </div>
      </HudPanel>
    );
  }

  const score = metrics.quality_score;
  const scoreColor = barColor(score);

  const components = [
    { label: "CALIBRATION", value: metrics.calibration_component },
    { label: "CONFIDENCE", value: metrics.confidence_component },
    { label: "STABILITY", value: metrics.stability_component },
    { label: "DATA QUALITY", value: metrics.data_quality_component },
    { label: "REGIME", value: metrics.regime_component },
  ];

  return (
    <HudPanel>
      <div className="p-2 space-y-2.5">
        {/* SECTION 2: Score */}
        <HudLabel>DECISION QUALITY</HudLabel>
        <div className="flex items-baseline gap-1">
          <span className="text-xl font-bold font-mono" style={{ color: scoreColor }}>
            {(score * 100).toFixed(1)}
          </span>
          <span className="font-mono text-[9px] text-muted-foreground/50">/ 100</span>
        </div>
        <ThinBar value={score * 100} color={scoreColor} />

        <div className="border-t border-hud-border/20" />

        {/* SECTION 3: Component Bars */}
        <div className="space-y-1.5">
          {components.map((c) => {
            const pct = c.value * 100;
            const col = barColor(c.value);
            return (
              <div key={c.label}>
                <div className="flex items-center justify-between mb-0.5">
                  <MetricTooltip term={c.label}>
                    <span className="font-mono text-[7px] tracking-[1px] text-muted-foreground">{c.label}</span>
                  </MetricTooltip>
                  <span className="font-mono text-[9px] font-bold" style={{ color: col }}>
                    {pct.toFixed(0)}
                  </span>
                </div>
                <ThinBar value={pct} color={col} />
              </div>
            );
          })}
        </div>
      </div>
    </HudPanel>
  );
});

// ---------------------------------------------------------------------------
// Connection Status
// ---------------------------------------------------------------------------

interface ConnectionStatusProps {
  connected: boolean;
  checking: boolean;
}

export function ConnectionStatus({ connected, checking }: ConnectionStatusProps) {
  if (checking) {
    return (
      <div className="flex items-center gap-2 text-[9px] text-muted-foreground font-mono">
        <div className="w-1.5 h-1.5 rounded-full bg-hud-amber animate-pulse" />
        CONNECTING...
      </div>
    );
  }
  return (
    <div className="flex items-center gap-2 text-[9px] font-mono">
      <div className={`w-1.5 h-1.5 rounded-full ${connected ? "bg-hud-green animate-pulse-live" : "bg-hud-red"}`} />
      <span className={connected ? "text-hud-green" : "text-hud-red"}>
        {connected ? "BACKEND CONNECTED" : "BACKEND OFFLINE"}
      </span>
    </div>
  );
}
