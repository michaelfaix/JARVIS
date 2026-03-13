// =============================================================================
// src/components/dashboard/system-status.tsx — Unified System Mode Widget
// =============================================================================

"use client";

import React from "react";
import { HudPanel } from "@/components/ui/hud-panel";
import { Skeleton } from "@/components/ui/skeleton";
import { MetricTooltip } from "@/components/ui/metric-tooltip";
import { MODUS_COLORS } from "@/lib/types";
import type { MetricsResponse } from "@/lib/api";
import type { Signal } from "@/lib/types";

const F = "'Courier New', Courier, monospace";

function L({ children }: { children: React.ReactNode }) {
  return <span style={{ fontFamily: F }} className="text-[7px] tracking-[2px] text-[#2a3a52] uppercase block">{children}</span>;
}

function Bar({ value, color, h = 3 }: { value: number; color: string; h?: number }) {
  return (
    <div className="w-full rounded-full overflow-hidden" style={{ height: h, backgroundColor: "#0d1a2d" }}>
      <div className="h-full rounded-full" style={{ width: `${Math.min(100, Math.max(1, value))}%`, backgroundColor: color, boxShadow: `0 0 4px ${color}60`, transition: "width 0.5s" }} />
    </div>
  );
}

function bc(v: number): string {
  return v >= 0.8 ? "#00e5a0" : v >= 0.6 ? "#ffaa00" : "#ff4466";
}

const STRATEGY_LABELS: Record<string, string> = {
  momentum: "MOMENTUM", mean_reversion: "MEAN REV", combined: "COMBINED",
  scalping: "SCALPING", custom: "CUSTOM",
};

// ---------------------------------------------------------------------------
// SystemModeCard — The unified left-column widget
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
  // New props for trade readiness
  selectedAsset?: string;
  selectedStrategy?: string;
  signals?: Signal[];
  totalValue?: number;
}

export const SystemModeCard = React.memo(function SystemModeCard({
  modus, vorhersagenAktiv, konfidenzMultiplikator, entscheidungsCount,
  ece, oodScore, metaUncertainty, loading, backendOnline = false,
  selectedAsset, selectedStrategy, signals = [], totalValue = 100000,
}: SystemModeCardProps) {
  const color = MODUS_COLORS[modus] || "#6b7280";

  // Find signal for selected asset
  const assetSignal = selectedAsset
    ? signals.find((s) => s.asset === selectedAsset) ?? signals[0]
    : signals[0];

  // Compute trade readiness
  const signalStrength = assetSignal ? assetSignal.confidence * 100 : 0;
  const riskLevel = oodScore > 0.5 || ece > 0.15 ? "HIGH" : oodScore > 0.3 || ece > 0.08 ? "MEDIUM" : "LOW";
  const riskColor = riskLevel === "LOW" ? "#00e5a0" : riskLevel === "MEDIUM" ? "#ffaa00" : "#ff4466";
  const strategyFit = modus === "NORMAL" ? 85 : modus === "ERHOEHTE_VORSICHT" ? 60 : 30;
  const positionPct = Math.max(0, Math.min(5, assetSignal ? assetSignal.confidence * (1 - oodScore) * 5 : 0));
  const positionValue = totalValue * (positionPct / 100);

  return (
    <HudPanel>
      <div className="p-2 space-y-2" style={{ fontFamily: F }}>
        {loading ? (
          <div className="space-y-2">
            <Skeleton className="h-4 w-24" />
            {[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-3 w-full" />)}
          </div>
        ) : (
          <>
            {/* 1. HEADER */}
            <div className="flex items-center justify-between">
              <L>SYSTEM MODE</L>
              <div className="flex items-center gap-1">
                <div className="w-1.5 h-1.5 rounded-full animate-pulse-live" style={{ backgroundColor: backendOnline ? "#00e5a0" : "#ff4466" }} />
                <span className="text-[7px] tracking-[1px]" style={{ color: backendOnline ? "#00e5a0" : "#ff4466" }}>
                  {backendOnline ? "LIVE" : "OFF"}
                </span>
              </div>
            </div>

            <div className="border-t border-[#0d1a2d]" />

            {/* 3. DECISION QUALITY */}
            <div>
              <L>DECISION QUALITY</L>
              <div className="flex items-center justify-between mt-1">
                <div className="flex items-baseline gap-0.5">
                  <span className="text-lg font-bold text-hud-cyan">{(konfidenzMultiplikator * 93.8).toFixed(1)}</span>
                  <span className="text-[8px] text-[#2a3a52]">/100</span>
                </div>
                <span className="text-[7px] px-1.5 py-0.5 rounded border text-[#2a3a52]" style={{ borderColor: color, color }}>
                  {modus === "NORMAL" ? "NORMAL" : modus.replace(/_/g, " ")}
                </span>
              </div>
              <div className="mt-1">
                <Bar value={konfidenzMultiplikator * 93.8} color={bc(konfidenzMultiplikator * 0.938)} />
              </div>
            </div>

            {/* 4. SUB-BARS */}
            <div className="space-y-1.5">
              <SubBar label="CALIBRATION" value={(1 - ece * 5) * 100} />
              <SubBar label="CONFIDENCE" value={konfidenzMultiplikator * 88} />
              <SubBar label="STABILITY" value={metaUncertainty < 0.1 ? 100 : metaUncertainty < 0.3 ? 70 : 40} />
              <SubBar label="REGIME" value={oodScore < 0.3 ? 90 : oodScore < 0.5 ? 74 : 40} />
            </div>

            <div className="border-t border-[#0d1a2d]" />

            {/* 6. ML METRIKEN */}
            <div>
              <L>ML METRIKEN</L>
              <div className="grid grid-cols-2 gap-x-2 gap-y-1 mt-1">
                <MetricTooltip term="ECE">
                  <div>
                    <span className="text-[6px] tracking-[1px] text-[#2a3a52] uppercase block">ECE</span>
                    <span className={`text-[9px] font-bold ${ece > 0.08 ? "text-hud-amber" : "text-hud-green"}`}>{ece.toFixed(4)}</span>
                  </div>
                </MetricTooltip>
                <MetricTooltip term="OOD Score">
                  <div>
                    <span className="text-[6px] tracking-[1px] text-[#2a3a52] uppercase block">OOD</span>
                    <span className={`text-[9px] font-bold ${oodScore > 0.5 ? "text-hud-red" : oodScore > 0.3 ? "text-hud-amber" : "text-hud-green"}`}>{oodScore.toFixed(3)}</span>
                  </div>
                </MetricTooltip>
                <MetricTooltip term="Meta Uncertainty">
                  <div>
                    <span className="text-[6px] tracking-[1px] text-[#2a3a52] uppercase block">META-U</span>
                    <span className="text-[9px] font-bold text-white">{metaUncertainty.toFixed(3)}</span>
                  </div>
                </MetricTooltip>
                <div>
                  <span className="text-[6px] tracking-[1px] text-[#2a3a52] uppercase block">RISK</span>
                  <span className="text-[9px] font-bold" style={{ color: riskColor }}>{riskLevel}</span>
                </div>
              </div>
            </div>

            <div className="border-t border-[#0d1a2d]" />

            {/* 8. AKTIVES ASSET & STRATEGIE */}
            {selectedAsset && (
              <div>
                <L>AKTIVES ASSET</L>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-[10px] font-bold text-white">{selectedAsset}</span>
                  <span className="text-[7px] px-1 py-0.5 rounded bg-hud-cyan/10 text-hud-cyan border border-hud-cyan/30">
                    {STRATEGY_LABELS[selectedStrategy ?? "combined"] ?? "COMBINED"}
                  </span>
                </div>
                <div className="mt-1.5 space-y-1">
                  <SubBar label="STRATEGIE-FIT" value={strategyFit} />
                  <SubBar label="SIGNAL STÄRKE" value={signalStrength} />
                </div>
              </div>
            )}

            {/* 9. EMPFEHLUNG */}
            {assetSignal && (
              <>
                <div className="border-t border-[#0d1a2d]" />
                <div className="rounded border p-1.5 space-y-1" style={{ borderColor: assetSignal.direction === "LONG" ? "#00e5a030" : "#ff446630" }}>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold" style={{ color: assetSignal.direction === "LONG" ? "#00e5a0" : "#ff4466" }}>
                      {assetSignal.direction === "LONG" ? "▲ LONG" : "▼ SHORT"}
                    </span>
                    <span className="text-[9px] font-bold text-hud-cyan">{(assetSignal.confidence * 100).toFixed(0)}%</span>
                  </div>
                  <div className="grid grid-cols-2 gap-x-2 gap-y-0.5 text-[7px]">
                    <div><span className="text-[#2a3a52]">ENTRY </span><span className="text-white">${assetSignal.entry.toLocaleString("en-US", { maximumFractionDigits: 0 })}</span></div>
                    <div><span className="text-[#2a3a52]">SL </span><span className="text-hud-red">${assetSignal.stopLoss.toLocaleString("en-US", { maximumFractionDigits: 0 })}</span></div>
                    <div><span className="text-[#2a3a52]">TP </span><span className="text-hud-green">${assetSignal.takeProfit.toLocaleString("en-US", { maximumFractionDigits: 0 })}</span></div>
                    <div><span className="text-[#2a3a52]">R:R </span><span className="text-hud-cyan">1:{((assetSignal.takeProfit - assetSignal.entry) / Math.abs(assetSignal.entry - assetSignal.stopLoss) || 0).toFixed(1)}</span></div>
                  </div>
                  <div className="flex items-center justify-between pt-0.5 border-t border-[#0d1a2d]">
                    <span className="text-[6px] tracking-[1px] text-[#2a3a52] uppercase">POSITION</span>
                    <span className="text-[8px] font-bold text-white">{positionPct.toFixed(2)}% — €{positionValue.toFixed(0)}</span>
                  </div>
                </div>
              </>
            )}

            {/* 10. FOOTER */}
            <div className="flex items-center justify-between pt-0.5 text-[7px] text-[#2a3a52]">
              <span>{entscheidungsCount.toLocaleString()} DECISIONS</span>
              <span style={{ color: vorhersagenAktiv ? "#00e5a0" : "#ff4466" }}>
                {vorhersagenAktiv ? "● ACTIVE" : "● OFF"}
              </span>
            </div>
          </>
        )}
      </div>
    </HudPanel>
  );
});

function SubBar({ label, value }: { label: string; value: number }) {
  const col = bc(value / 100);
  return (
    <div>
      <div className="flex items-center justify-between mb-0.5">
        <span className="text-[6px] tracking-[1.5px] text-[#2a3a52] uppercase">{label}</span>
        <span className="text-[8px] font-bold" style={{ color: col }}>{value.toFixed(0)}</span>
      </div>
      <Bar value={value} color={col} h={2} />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Quality Score Card (kept for right column)
// ---------------------------------------------------------------------------

interface QualityScoreCardProps {
  metrics: MetricsResponse | null;
  loading?: boolean;
}

export const QualityScoreCard = React.memo(function QualityScoreCard({ metrics, loading }: QualityScoreCardProps) {
  if (!metrics || loading) {
    return (
      <HudPanel>
        <div className="p-2 space-y-2" style={{ fontFamily: F }}>
          <L>DECISION QUALITY</L>
          <Skeleton className="h-7 w-20" />
          <Skeleton className="h-[2px] w-full" />
          {[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-3 w-full" />)}
        </div>
      </HudPanel>
    );
  }

  const score = metrics.quality_score;
  const scoreColor = bc(score);

  const components = [
    { label: "CALIBRATION", value: metrics.calibration_component },
    { label: "CONFIDENCE", value: metrics.confidence_component },
    { label: "STABILITY", value: metrics.stability_component },
    { label: "DATA QUALITY", value: metrics.data_quality_component },
    { label: "REGIME", value: metrics.regime_component },
  ];

  return (
    <HudPanel>
      <div className="p-2 space-y-2" style={{ fontFamily: F }}>
        <L>DECISION QUALITY</L>
        <div className="flex items-baseline gap-0.5 mt-1">
          <span className="text-xl font-bold text-hud-cyan">{(score * 100).toFixed(1)}</span>
          <span className="text-[9px] text-[#2a3a52]">/100</span>
        </div>
        <Bar value={score * 100} color={scoreColor} />
        <div className="border-t border-[#0d1a2d] mt-1 mb-0.5" />
        <div className="space-y-1.5">
          {components.map((c) => (
            <SubBar key={c.label} label={c.label} value={c.value * 100} />
          ))}
        </div>
      </div>
    </HudPanel>
  );
});

// ---------------------------------------------------------------------------
// Connection Status
// ---------------------------------------------------------------------------

export function ConnectionStatus({ connected, checking }: { connected: boolean; checking: boolean }) {
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
