// =============================================================================
// src/app/(app)/page.tsx — Dashboard Page
// =============================================================================

"use client";

import { BTCChart } from "@/components/chart/btc-chart";
import { RegimeDisplay } from "@/components/dashboard/regime-display";
import {
  QualityScoreCard,
  SystemModeCard,
} from "@/components/dashboard/system-status";
import { StatCard } from "@/components/dashboard/stat-card";
import { AppHeader } from "@/components/layout/app-header";
import { useMetrics, useSystemStatus } from "@/hooks/use-jarvis";
import { inferRegime, type RegimeState } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function DashboardPage() {
  const { status } = useSystemStatus(5000);
  const { metrics } = useMetrics(5000);

  const regime: RegimeState = status
    ? inferRegime(status.modus)
    : "RISK_ON";

  return (
    <>
      <AppHeader title="Dashboard" subtitle="Market Overview" />
      <div className="p-6 space-y-6">
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
              <span className="text-xs font-normal">Synthetic demo data</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <BTCChart regime={regime} height={450} />
          </CardContent>
        </Card>

        {/* Stats Row */}
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
          <StatCard label="System Uptime" value="100%" />
        </div>
      </div>
    </>
  );
}
