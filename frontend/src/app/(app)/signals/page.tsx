// =============================================================================
// src/app/(app)/signals/page.tsx — Live Signal Feed
// =============================================================================

"use client";

import { AppHeader } from "@/components/layout/app-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Progress } from "@/components/ui/progress";
import { useSignals } from "@/hooks/use-signals";
import { useSystemStatus } from "@/hooks/use-jarvis";
import { inferRegime } from "@/lib/types";
import { DEFAULT_ASSETS } from "@/lib/constants";
import { AlertTriangle, Radio, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function SignalsPage() {
  const { status } = useSystemStatus(5000);
  const regime = status ? inferRegime(status.modus) : "RISK_ON";
  const { signals, loading, error, refresh } = useSignals(regime, 10000);

  const activeLongs = signals.filter((s) => s.direction === "LONG").length;
  const activeShorts = signals.filter((s) => s.direction === "SHORT").length;
  const avgConfidence =
    signals.length > 0
      ? signals.reduce((sum, s) => sum + s.confidence, 0) / signals.length
      : 0;

  return (
    <>
      <AppHeader title="Signals" subtitle="Live Signal Feed" />
      <div className="p-6 space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="text-xs text-muted-foreground mb-1">
                Active Signals
              </div>
              <div className="text-2xl font-bold font-mono text-white">
                {signals.length}
              </div>
            </CardContent>
          </Card>
          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="text-xs text-muted-foreground mb-1">
                Long / Short
              </div>
              <div className="text-xl font-bold font-mono">
                <span className="text-green-400">{activeLongs}</span>
                <span className="text-muted-foreground mx-1">/</span>
                <span className="text-red-400">{activeShorts}</span>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="text-xs text-muted-foreground mb-1">
                Avg Confidence
              </div>
              <div className="text-xl font-bold font-mono text-white">
                {(avgConfidence * 100).toFixed(1)}%
              </div>
            </CardContent>
          </Card>
          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="text-xs text-muted-foreground mb-1">Regime</div>
              <div className="text-xl font-bold font-mono text-blue-400">
                {regime.replace("_", " ")}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Signal Feed Table */}
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <Radio className="h-4 w-4" />
                Signal Feed
                {loading && (
                  <RefreshCw className="h-3 w-3 animate-spin text-blue-400" />
                )}
              </CardTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={refresh}
                className="h-7 text-xs"
              >
                <RefreshCw className="h-3 w-3 mr-1" />
                Refresh
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {error && (
              <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">
                {error}. Backend may be offline.
              </div>
            )}

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Asset</TableHead>
                  <TableHead>Direction</TableHead>
                  <TableHead className="text-right">Entry</TableHead>
                  <TableHead className="text-right">Stop Loss</TableHead>
                  <TableHead className="text-right">Take Profit</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead className="text-right">Quality</TableHead>
                  <TableHead>OOD</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {signals.length === 0 && !loading ? (
                  <TableRow>
                    <TableCell
                      colSpan={8}
                      className="text-center text-muted-foreground py-8"
                    >
                      {error
                        ? "Connect backend to see signals"
                        : "No signals available"}
                    </TableCell>
                  </TableRow>
                ) : (
                  signals.map((signal) => {
                    const asset = DEFAULT_ASSETS.find(
                      (a) => a.symbol === signal.asset
                    );
                    return (
                      <TableRow key={signal.id}>
                        <TableCell>
                          <div>
                            <div className="font-medium text-white">
                              {signal.asset}
                            </div>
                            <div className="text-[10px] text-muted-foreground">
                              {asset?.name}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge
                            className={
                              signal.direction === "LONG"
                                ? "bg-green-500/20 text-green-400 border-green-500/30"
                                : "bg-red-500/20 text-red-400 border-red-500/30"
                            }
                          >
                            {signal.direction}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right font-mono text-white">
                          ${signal.entry.toLocaleString("en-US", {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </TableCell>
                        <TableCell className="text-right font-mono text-red-400">
                          ${signal.stopLoss.toLocaleString("en-US", {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </TableCell>
                        <TableCell className="text-right font-mono text-green-400">
                          ${signal.takeProfit.toLocaleString("en-US", {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2 w-32">
                            <Progress
                              value={signal.confidence * 100}
                              className="h-1.5"
                              indicatorClassName={
                                signal.confidence > 0.7
                                  ? "bg-green-500"
                                  : signal.confidence > 0.4
                                  ? "bg-yellow-500"
                                  : "bg-red-500"
                              }
                            />
                            <span className="text-xs font-mono text-muted-foreground w-10 text-right">
                              {(signal.confidence * 100).toFixed(0)}%
                            </span>
                          </div>
                        </TableCell>
                        <TableCell className="text-right font-mono">
                          <span
                            className={
                              signal.qualityScore > 0.7
                                ? "text-green-400"
                                : signal.qualityScore > 0.4
                                ? "text-yellow-400"
                                : "text-red-400"
                            }
                          >
                            {(signal.qualityScore * 100).toFixed(0)}
                          </span>
                        </TableCell>
                        <TableCell>
                          {signal.isOod && (
                            <AlertTriangle className="h-4 w-4 text-yellow-500" />
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
