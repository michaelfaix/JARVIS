// =============================================================================
// src/components/dashboard/system-status.tsx — System Status Cards (HUD)
// =============================================================================

"use client";

import { HudPanel } from "@/components/ui/hud-panel";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { MetricTooltip } from "@/components/ui/metric-tooltip";
import { MODUS_COLORS } from "@/lib/types";
import type { MetricsResponse } from "@/lib/api";

// ---------------------------------------------------------------------------
// System Mode Card
// ---------------------------------------------------------------------------

const MODUS_SEVERITY: Record<string, number> = {
  NORMAL: 0,
  ERHOEHTE_VORSICHT: 1,
  REDUZIERTES_VERTRAUEN: 2,
  MINIMALE_EXPOSITION: 3,
  NUR_MONITORING: 4,
  NOTFALL_MODUS: 5,
  DATEN_QUARANTAENE: 6,
  MODELL_ROLLBACK: 7,
  KONFIDENZ_KOLLAPS: 8,
};

const MODUS_LABELS: Record<string, string> = {
  NORMAL: "Normal",
  ERHOEHTE_VORSICHT: "Erhöhte Vorsicht",
  REDUZIERTES_VERTRAUEN: "Reduz. Vertrauen",
  MINIMALE_EXPOSITION: "Min. Exposition",
  NUR_MONITORING: "Nur Monitoring",
  NOTFALL_MODUS: "Notfall",
  DATEN_QUARANTAENE: "Daten-Quarantäne",
  MODELL_ROLLBACK: "Modell Rollback",
  KONFIDENZ_KOLLAPS: "Konfidenz-Kollaps",
};

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

export function SystemModeCard({
  modus,
  vorhersagenAktiv,
  konfidenzMultiplikator,
  entscheidungsCount,
  ece,
  oodScore,
  metaUncertainty,
  loading,
  backendOnline = false,
}: SystemModeCardProps) {
  const color = MODUS_COLORS[modus] || "#6b7280";
  const label = MODUS_LABELS[modus] || modus.replace(/_/g, " ");
  const severity = MODUS_SEVERITY[modus] ?? 0;
  const severityPct = Math.min(100, (severity / 8) * 100);
  const confReduced = konfidenzMultiplikator < 0.95;

  return (
    <HudPanel title="System Mode">
      <div className="p-2.5 space-y-2">
        {loading ? (
          <>
            <Skeleton className="h-6 w-28" />
            <Skeleton className="h-1.5 w-full" />
            <div className="space-y-1.5">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-3.5 w-full" />
              ))}
            </div>
          </>
        ) : (
          <>
            {/* Mode name */}
            <div className="flex items-center gap-2">
              <div
                className="w-2.5 h-2.5 rounded-full shrink-0"
                style={{
                  backgroundColor: color,
                  boxShadow: severity >= 5 ? `0 0 8px ${color}` : "none",
                  animation: severity >= 5 ? "pulseLive 2s infinite" : "none",
                }}
              />
              <span className="text-sm font-bold font-mono truncate" style={{ color }}>
                {label}
              </span>
              <Badge
                className="ml-auto text-[8px] border font-mono"
                style={{
                  backgroundColor: `${color}15`,
                  color: color,
                  borderColor: `${color}40`,
                }}
              >
                {backendOnline ? "Live" : "Off"}
              </Badge>
            </div>

            {/* Severity bar */}
            <div>
              <div className="flex items-center justify-between text-[8px] font-mono text-muted-foreground mb-0.5">
                <span>Severity</span>
                <span>{severity}/8</span>
              </div>
              <div className="w-full h-1 bg-hud-bg rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{
                    width: `${severityPct}%`,
                    background: "linear-gradient(90deg, #00e5a0, #ffaa00, #ff4466)",
                  }}
                />
              </div>
            </div>

            {/* Metrics */}
            <div className="space-y-1">
              <MetricRow label="Predictions" tooltip="Predictions">
                <Badge className={`text-[8px] font-mono ${vorhersagenAktiv ? "bg-hud-green/20 text-hud-green border-hud-green/30" : "bg-hud-red/20 text-hud-red border-hud-red/30"}`}>
                  {vorhersagenAktiv ? "ACTIVE" : "OFF"}
                </Badge>
              </MetricRow>
              <MetricRow label="Conf." tooltip="Confidence">
                <span className={`font-mono text-[10px] ${confReduced ? "text-hud-amber" : "text-white"}`}>
                  {konfidenzMultiplikator.toFixed(2)}×
                </span>
              </MetricRow>
              <MetricRow label="ECE" tooltip="ECE">
                <span className={`font-mono text-[10px] ${ece > 0.15 ? "text-hud-red" : ece > 0.08 ? "text-hud-amber" : "text-hud-green"}`}>
                  {(ece * 100).toFixed(1)}%
                </span>
              </MetricRow>
              <MetricRow label="OOD" tooltip="OOD Score">
                <span className={`font-mono text-[10px] ${oodScore > 0.5 ? "text-hud-red" : oodScore > 0.3 ? "text-hud-amber" : "text-hud-green"}`}>
                  {(oodScore * 100).toFixed(0)}%
                </span>
              </MetricRow>
              <MetricRow label="Meta-U" tooltip="Meta Uncertainty">
                <span className={`font-mono text-[10px] ${metaUncertainty > 0.5 ? "text-hud-red" : metaUncertainty > 0.3 ? "text-hud-amber" : "text-hud-green"}`}>
                  {(metaUncertainty * 100).toFixed(0)}%
                </span>
              </MetricRow>
              <div className="flex items-center justify-between text-[10px] pt-1 border-t border-hud-border/30">
                <span className="text-muted-foreground font-mono">Decisions</span>
                <span className="font-mono text-white">{entscheidungsCount.toLocaleString()}</span>
              </div>
            </div>
          </>
        )}
      </div>
    </HudPanel>
  );
}

function MetricRow({ label, tooltip, children }: { label: string; tooltip: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between text-[10px]">
      <MetricTooltip term={tooltip}>
        <span className="text-muted-foreground font-mono">{label}</span>
      </MetricTooltip>
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Quality Score Card
// ---------------------------------------------------------------------------

interface QualityScoreCardProps {
  metrics: MetricsResponse | null;
  loading?: boolean;
}

export function QualityScoreCard({ metrics, loading }: QualityScoreCardProps) {
  if (!metrics || loading) {
    return (
      <HudPanel title="Decision Quality">
        <div className="p-2.5 space-y-2">
          <Skeleton className="h-8 w-20" />
          <Skeleton className="h-1.5 w-full" />
          <div className="space-y-1.5">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-3 w-full" />
            ))}
          </div>
        </div>
      </HudPanel>
    );
  }

  const score = metrics.quality_score;
  const scoreColor = score >= 0.8 ? "#00e5a0" : score >= 0.5 ? "#ffaa00" : "#ff4466";

  const components = [
    { label: "Calibration", value: metrics.calibration_component, weight: 0.35 },
    { label: "Confidence", value: metrics.confidence_component, weight: 0.25 },
    { label: "Stability", value: metrics.stability_component, weight: 0.2 },
    { label: "Data Qual.", value: metrics.data_quality_component, weight: 0.1 },
    { label: "Regime", value: metrics.regime_component, weight: 0.1 },
  ];

  return (
    <HudPanel title="Decision Quality">
      <div className="p-2.5 space-y-2">
        <div className="flex items-baseline gap-1.5">
          <span className="text-2xl font-bold font-mono" style={{ color: scoreColor }}>
            {(score * 100).toFixed(1)}
          </span>
          <span className="text-[10px] text-muted-foreground font-mono">/ 100</span>
        </div>

        <div className="w-full h-1.5 bg-hud-bg rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{ width: `${score * 100}%`, backgroundColor: scoreColor }}
          />
        </div>

        <div className="space-y-1">
          {components.map((c) => (
            <div key={c.label} className="flex items-center gap-1.5 text-[10px]">
              <MetricTooltip term={c.label}>
                <span className="text-muted-foreground font-mono w-16 shrink-0">{c.label}</span>
              </MetricTooltip>
              <div className="flex-1 h-1 bg-hud-bg rounded-full overflow-hidden">
                <div className="h-full rounded-full bg-hud-cyan/60" style={{ width: `${c.value * 100}%` }} />
              </div>
              <span className="font-mono text-muted-foreground w-6 text-right">
                {(c.value * 100).toFixed(0)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </HudPanel>
  );
}

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
      <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono">
        <div className="w-2 h-2 rounded-full bg-hud-amber animate-pulse" />
        Connecting to JARVIS...
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 text-xs font-mono">
      <div className={`w-2 h-2 rounded-full ${connected ? "bg-hud-green" : "bg-hud-red"}`} />
      <span className={connected ? "text-hud-green" : "text-hud-red"}>
        {connected ? "Backend Connected" : "Backend Offline"}
      </span>
    </div>
  );
}
