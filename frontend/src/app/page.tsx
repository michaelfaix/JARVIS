// =============================================================================
// src/app/page.tsx — JARVIS Dashboard
//
// Main dashboard with:
// - Market Regime display
// - BTC/USD Chart with signal overlay
// - System status cards
// - Decision quality metrics
// =============================================================================

"use client";

import { BTCChart } from "@/components/chart/btc-chart";
import { RegimeDisplay } from "@/components/dashboard/regime-display";
import {
  ConnectionStatus,
  QualityScoreCard,
  SystemModeCard,
} from "@/components/dashboard/system-status";
import { useBackendHealth, useMetrics, useSystemStatus } from "@/hooks/use-jarvis";
import type { RegimeState } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function Dashboard() {
  const { connected, checking } = useBackendHealth();
  const { status } = useSystemStatus(5000);
  const { metrics } = useMetrics(5000);

  // Derive regime from status or default
  const regime: RegimeState = connected && status
    ? inferRegime(status.modus)
    : "RISK_ON";

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border/50 bg-card/30">
        <div className="max-w-[1600px] mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-white text-sm">
              J
            </div>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight">
                JARVIS Trader
              </h1>
              <p className="text-xs text-muted-foreground">
                Decision Quality Platform v7.0
              </p>
            </div>
          </div>
          <ConnectionStatus connected={connected} checking={checking} />
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1600px] mx-auto px-6 py-6 space-y-6">
        {/* Top Row: Regime + System Mode + Quality */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <RegimeDisplay
            regime={regime}
            metaUncertainty={status?.meta_unsicherheit ?? 0}
            ece={status?.ece ?? 0}
            oodScore={status?.ood_score ?? 0}
          />
          <SystemModeCard
            modus={status?.modus ?? "NORMAL"}
            vorhersagenAktiv={status?.vorhersagen_aktiv ?? true}
            konfidenzMultiplikator={status?.konfidenz_multiplikator ?? 1.0}
            entscheidungsCount={status?.entscheidungs_count ?? 0}
          />
          <QualityScoreCard metrics={metrics} />
        </div>

        {/* Chart */}
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center justify-between">
              <span>BTC/USD — 90 Day Chart with JARVIS Signals</span>
              <span className="text-xs font-normal">
                Synthetic data for demonstration
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <BTCChart regime={regime} height={500} />
          </CardContent>
        </Card>

        {/* Bottom Row: Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            label="Predictions Today"
            value={status?.entscheidungs_count?.toString() ?? "0"}
          />
          <StatCard
            label="Model Calibration"
            value={
              metrics
                ? `${(metrics.calibration_component * 100).toFixed(1)}%`
                : "—"
            }
          />
          <StatCard
            label="Data Quality"
            value={
              metrics
                ? `${(metrics.data_quality_component * 100).toFixed(1)}%`
                : "—"
            }
          />
          <StatCard
            label="System Uptime"
            value="100%"
          />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border/50 mt-8">
        <div className="max-w-[1600px] mx-auto px-6 py-4 text-xs text-muted-foreground flex justify-between">
          <span>JARVIS MASP v7.0 — Analysis & Research Platform</span>
          <span>Not a trading system. No real money. No broker API.</span>
        </div>
      </footer>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function inferRegime(modus: string): RegimeState {
  switch (modus) {
    case "NORMAL":
      return "RISK_ON";
    case "ERHOEHTE_VORSICHT":
    case "REDUZIERTES_VERTRAUEN":
      return "RISK_OFF";
    case "NOTFALL_MODUS":
    case "KONFIDENZ_KOLLAPS":
      return "CRISIS";
    case "MINIMALE_EXPOSITION":
    case "NUR_MONITORING":
      return "TRANSITION";
    default:
      return "RISK_ON";
  }
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <Card className="bg-card/50 border-border/50">
      <CardContent className="pt-4 pb-3 px-4">
        <div className="text-xs text-muted-foreground mb-1">{label}</div>
        <div className="text-xl font-bold font-mono text-white">{value}</div>
      </CardContent>
    </Card>
  );
}
