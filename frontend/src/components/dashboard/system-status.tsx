// =============================================================================
// src/components/dashboard/system-status.tsx — System Status Cards
// =============================================================================

"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MODUS_COLORS } from "@/lib/types";
import type { MetricsResponse } from "@/lib/api";

// ---------------------------------------------------------------------------
// System Mode Card
// ---------------------------------------------------------------------------

interface SystemModeCardProps {
  modus: string;
  vorhersagenAktiv: boolean;
  konfidenzMultiplikator: number;
  entscheidungsCount: number;
}

export function SystemModeCard({
  modus,
  vorhersagenAktiv,
  konfidenzMultiplikator,
  entscheidungsCount,
}: SystemModeCardProps) {
  const color = MODUS_COLORS[modus] || "#6b7280";
  const modusLabel = modus.replace(/_/g, " ");

  return (
    <Card className="bg-card/50 border-border/50">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          System Mode
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-2">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: color }}
          />
          <span className="text-lg font-bold" style={{ color }}>
            {modusLabel}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Predictions</span>
            <Badge
              variant={vorhersagenAktiv ? "default" : "destructive"}
              className="text-[10px]"
            >
              {vorhersagenAktiv ? "ACTIVE" : "DISABLED"}
            </Badge>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Confidence</span>
            <span className="font-mono text-white">
              {(konfidenzMultiplikator * 100).toFixed(0)}%
            </span>
          </div>
          <div className="col-span-2 flex justify-between">
            <span className="text-muted-foreground">Decisions</span>
            <span className="font-mono text-white">
              {entscheidungsCount.toLocaleString()}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Quality Score Card
// ---------------------------------------------------------------------------

interface QualityScoreCardProps {
  metrics: MetricsResponse | null;
}

export function QualityScoreCard({ metrics }: QualityScoreCardProps) {
  if (!metrics) {
    return (
      <Card className="bg-card/50 border-border/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Quality Score
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-muted-foreground text-sm">Loading...</div>
        </CardContent>
      </Card>
    );
  }

  const score = metrics.quality_score;
  const scoreColor =
    score >= 0.8 ? "#22c55e" : score >= 0.5 ? "#eab308" : "#ef4444";

  const components = [
    { label: "Calibration", value: metrics.calibration_component, weight: 0.35 },
    { label: "Confidence", value: metrics.confidence_component, weight: 0.25 },
    { label: "Stability", value: metrics.stability_component, weight: 0.2 },
    { label: "Data Quality", value: metrics.data_quality_component, weight: 0.1 },
    { label: "Regime", value: metrics.regime_component, weight: 0.1 },
  ];

  return (
    <Card className="bg-card/50 border-border/50">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Decision Quality
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Overall Score */}
        <div className="flex items-baseline gap-2">
          <span
            className="text-3xl font-bold font-mono"
            style={{ color: scoreColor }}
          >
            {(score * 100).toFixed(1)}
          </span>
          <span className="text-sm text-muted-foreground">/ 100</span>
        </div>

        {/* Progress bar */}
        <div className="w-full h-2 bg-background/50 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${score * 100}%`,
              backgroundColor: scoreColor,
            }}
          />
        </div>

        {/* Components */}
        <div className="space-y-1.5">
          {components.map((c) => (
            <div key={c.label} className="flex items-center gap-2 text-xs">
              <span className="text-muted-foreground w-24">{c.label}</span>
              <div className="flex-1 h-1.5 bg-background/50 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full bg-blue-500/70"
                  style={{ width: `${c.value * 100}%` }}
                />
              </div>
              <span className="font-mono text-muted-foreground w-8 text-right">
                {(c.value * 100).toFixed(0)}
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
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
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <div className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse" />
        Connecting to JARVIS...
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 text-xs">
      <div
        className={`w-2 h-2 rounded-full ${
          connected ? "bg-green-500" : "bg-red-500"
        }`}
      />
      <span className={connected ? "text-green-400" : "text-red-400"}>
        {connected ? "Backend Connected" : "Backend Offline"}
      </span>
      {!connected && (
        <span className="text-muted-foreground ml-1">
          (Start: uvicorn jarvis.api.main:app --port 8000)
        </span>
      )}
    </div>
  );
}
