// =============================================================================
// src/app/(app)/portfolio/page.tsx — Paper Trading Portfolio
// =============================================================================

"use client";

import { AppHeader } from "@/components/layout/app-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Separator } from "@/components/ui/separator";
import { usePortfolio } from "@/hooks/use-portfolio";
import { useSystemStatus } from "@/hooks/use-jarvis";
import { inferRegime, REGIME_COLORS, type RegimeState } from "@/lib/types";
import {
  TrendingUp,
  TrendingDown,
  Wallet,
  ShieldAlert,
  X,
} from "lucide-react";

export default function PortfolioPage() {
  const { state, closePosition, resetPortfolio, unrealizedPnl, totalValue } =
    usePortfolio();
  const { status } = useSystemStatus(5000);
  const regime: RegimeState = status ? inferRegime(status.modus) : "RISK_ON";

  const totalPnl = state.realizedPnl + unrealizedPnl;
  const totalPnlPercent =
    state.totalCapital > 0 ? (totalPnl / state.totalCapital) * 100 : 0;

  // Risk score from system status
  const riskScore = status
    ? Math.min(
        100,
        Math.round(
          (status.ece * 200 +
            status.ood_score * 100 +
            status.meta_unsicherheit * 100) /
            3
        )
      )
    : 0;

  // Allocation by asset
  const allocation = state.positions.reduce<Record<string, number>>(
    (acc, pos) => {
      acc[pos.asset] = (acc[pos.asset] || 0) + pos.capitalAllocated;
      return acc;
    },
    {}
  );
  const allocatedTotal = Object.values(allocation).reduce(
    (sum, v) => sum + v,
    0
  );

  return (
    <>
      <AppHeader title="Portfolio" subtitle="Paper Trading Account" />
      <div className="p-6 space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                <Wallet className="h-3 w-3" /> Total Value
              </div>
              <div className="text-2xl font-bold font-mono text-white">
                $
                {totalValue.toLocaleString("en-US", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                {totalPnl >= 0 ? (
                  <TrendingUp className="h-3 w-3" />
                ) : (
                  <TrendingDown className="h-3 w-3" />
                )}
                Total P&L
              </div>
              <div
                className={`text-2xl font-bold font-mono ${
                  totalPnl >= 0 ? "text-green-400" : "text-red-400"
                }`}
              >
                {totalPnl >= 0 ? "+" : ""}$
                {Math.abs(totalPnl).toLocaleString("en-US", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </div>
              <div
                className={`text-xs font-mono ${
                  totalPnlPercent >= 0 ? "text-green-400" : "text-red-400"
                }`}
              >
                {totalPnlPercent >= 0 ? "+" : ""}
                {totalPnlPercent.toFixed(2)}%
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                <ShieldAlert className="h-3 w-3" /> Risk Score
              </div>
              <div
                className={`text-2xl font-bold font-mono ${
                  riskScore < 30
                    ? "text-green-400"
                    : riskScore < 60
                    ? "text-yellow-400"
                    : "text-red-400"
                }`}
              >
                {riskScore}
              </div>
              <div className="text-xs text-muted-foreground">
                {riskScore < 30
                  ? "Low Risk"
                  : riskScore < 60
                  ? "Moderate"
                  : "High Risk"}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="text-xs text-muted-foreground mb-1">
                Available Capital
              </div>
              <div className="text-2xl font-bold font-mono text-white">
                $
                {state.availableCapital.toLocaleString("en-US", {
                  minimumFractionDigits: 0,
                })}
              </div>
              <div className="text-xs text-muted-foreground">
                of ${state.totalCapital.toLocaleString()}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Asset Allocation */}
          <Card className="bg-card/50 border-border/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Asset Allocation
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {Object.entries(allocation).length === 0 ? (
                <div className="text-sm text-muted-foreground py-4 text-center">
                  No open positions
                </div>
              ) : (
                Object.entries(allocation).map(([asset, amount]) => {
                  const pct =
                    allocatedTotal > 0 ? (amount / allocatedTotal) * 100 : 0;
                  return (
                    <div key={asset}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-white font-medium">{asset}</span>
                        <span className="font-mono text-muted-foreground">
                          {pct.toFixed(1)}%
                        </span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-background/50 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-blue-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })
              )}
              <Separator className="opacity-50" />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Cash</span>
                <span className="font-mono">
                  $
                  {state.availableCapital.toLocaleString("en-US", {
                    minimumFractionDigits: 0,
                  })}
                </span>
              </div>
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Market Regime</span>
                <Badge
                  variant="outline"
                  className="text-[10px] px-1.5 py-0"
                  style={{
                    borderColor: REGIME_COLORS[regime],
                    color: REGIME_COLORS[regime],
                  }}
                >
                  {regime.replace("_", " ")}
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Open Positions Table */}
          <Card className="bg-card/50 border-border/50 lg:col-span-2">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Open Positions ({state.positions.length})
                </CardTitle>
                {state.positions.length > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs text-muted-foreground h-7"
                    onClick={() => resetPortfolio(state.totalCapital)}
                  >
                    Close All
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Asset</TableHead>
                    <TableHead>Side</TableHead>
                    <TableHead className="text-right">Size</TableHead>
                    <TableHead className="text-right">Entry</TableHead>
                    <TableHead className="text-right">Current</TableHead>
                    <TableHead className="text-right">P&L</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {state.positions.length === 0 ? (
                    <TableRow>
                      <TableCell
                        colSpan={7}
                        className="text-center text-muted-foreground py-8"
                      >
                        No open positions. Accept signals to open trades.
                      </TableCell>
                    </TableRow>
                  ) : (
                    state.positions.map((pos) => (
                      <TableRow key={pos.id}>
                        <TableCell className="font-medium text-white">
                          {pos.asset}
                        </TableCell>
                        <TableCell>
                          <Badge
                            className={
                              pos.direction === "LONG"
                                ? "bg-green-500/20 text-green-400 border-green-500/30"
                                : "bg-red-500/20 text-red-400 border-red-500/30"
                            }
                          >
                            {pos.direction}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right font-mono text-white">
                          {pos.size.toFixed(4)}
                        </TableCell>
                        <TableCell className="text-right font-mono text-muted-foreground">
                          ${pos.entryPrice.toLocaleString()}
                        </TableCell>
                        <TableCell className="text-right font-mono text-white">
                          ${pos.currentPrice.toLocaleString()}
                        </TableCell>
                        <TableCell
                          className={`text-right font-mono ${
                            pos.pnl >= 0 ? "text-green-400" : "text-red-400"
                          }`}
                        >
                          {pos.pnl >= 0 ? "+" : ""}$
                          {Math.abs(pos.pnl).toFixed(2)}
                          <div className="text-[10px]">
                            {pos.pnlPercent >= 0 ? "+" : ""}
                            {pos.pnlPercent.toFixed(2)}%
                          </div>
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 w-7 p-0 text-muted-foreground hover:text-red-400"
                            onClick={() => closePosition(pos.id)}
                          >
                            <X className="h-3 w-3" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
}
