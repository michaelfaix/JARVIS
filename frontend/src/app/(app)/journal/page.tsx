// =============================================================================
// src/app/(app)/journal/page.tsx — Trade Journal with filtering & analytics
// =============================================================================

"use client";

import React, { useMemo, useState } from "react";
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
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { usePortfolio } from "@/hooks/use-portfolio";
import { useTradeNotes, TAG_SUGGESTIONS } from "@/hooks/use-trade-notes";
import { TradeNoteEditor } from "@/components/journal/trade-note-editor";
import { TradeStatsDashboard } from "@/components/portfolio/trade-stats-dashboard";
import {
  BookOpen,
  TrendingUp,
  TrendingDown,
  Download,
  Filter,
  BarChart3,
  Clock,
  Target,
  DollarSign,
  StickyNote,
  Star,
} from "lucide-react";

type FilterAsset = "ALL" | string;
type FilterDirection = "ALL" | "LONG" | "SHORT";
type FilterResult = "ALL" | "WIN" | "LOSS";
type FilterTag = "ALL" | string;

export default function JournalPage() {
  const { state, winRate, avgWin, avgLoss, drawdown } = usePortfolio();
  const { notes } = useTradeNotes();
  const [filterAsset, setFilterAsset] = useState<FilterAsset>("ALL");
  const [filterDirection, setFilterDirection] = useState<FilterDirection>("ALL");
  const [filterResult, setFilterResult] = useState<FilterResult>("ALL");
  const [filterTag, setFilterTag] = useState<FilterTag>("ALL");
  const [editingTradeId, setEditingTradeId] = useState<string | null>(null);

  const allTrades = state.closedTrades;

  // Unique assets in trades
  const tradeAssets = useMemo(
    () => Array.from(new Set(allTrades.map((t) => t.asset))).sort(),
    [allTrades]
  );

  // Count noted trades
  const notedTradesCount = useMemo(
    () => allTrades.filter((t) => notes[t.id]).length,
    [allTrades, notes]
  );

  // Filtered trades
  const filtered = useMemo(() => {
    return allTrades.filter((t) => {
      if (filterAsset !== "ALL" && t.asset !== filterAsset) return false;
      if (filterDirection !== "ALL" && t.direction !== filterDirection) return false;
      if (filterResult === "WIN" && t.pnl <= 0) return false;
      if (filterResult === "LOSS" && t.pnl > 0) return false;
      if (filterTag !== "ALL") {
        const tradeNote = notes[t.id];
        if (!tradeNote || !tradeNote.tags.includes(filterTag)) return false;
      }
      return true;
    });
  }, [allTrades, filterAsset, filterDirection, filterResult, filterTag, notes]);

  // Stats for filtered set
  const stats = useMemo(() => {
    if (filtered.length === 0) return null;
    const wins = filtered.filter((t) => t.pnl > 0);
    const losses = filtered.filter((t) => t.pnl <= 0);
    const totalPnl = filtered.reduce((s, t) => s + t.pnl, 0);
    const wr = (wins.length / filtered.length) * 100;
    const aWin = wins.length > 0 ? wins.reduce((s, t) => s + t.pnl, 0) / wins.length : 0;
    const aLoss = losses.length > 0 ? losses.reduce((s, t) => s + t.pnl, 0) / losses.length : 0;
    const profitFactor =
      losses.length > 0 && Math.abs(losses.reduce((s, t) => s + t.pnl, 0)) > 0
        ? wins.reduce((s, t) => s + t.pnl, 0) / Math.abs(losses.reduce((s, t) => s + t.pnl, 0))
        : wins.length > 0
        ? Infinity
        : 0;
    const bestTrade = Math.max(...filtered.map((t) => t.pnl));
    const worstTrade = Math.min(...filtered.map((t) => t.pnl));
    const avgHoldTime = filtered.reduce((s, t) => {
      return s + (new Date(t.closedAt).getTime() - new Date(t.openedAt).getTime());
    }, 0) / filtered.length;

    return {
      total: filtered.length,
      wins: wins.length,
      losses: losses.length,
      totalPnl,
      winRate: wr,
      avgWin: aWin,
      avgLoss: aLoss,
      profitFactor,
      bestTrade,
      worstTrade,
      avgHoldTimeMs: avgHoldTime,
    };
  }, [filtered]);

  function formatDuration(ms: number): string {
    const mins = Math.floor(ms / 60000);
    if (mins < 60) return `${mins}m`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ${mins % 60}m`;
    const days = Math.floor(hours / 24);
    return `${days}d ${hours % 24}h`;
  }

  function csvEscape(val: string | number): string {
    return '"' + String(val).replace(/"/g, '""') + '"';
  }

  function exportCSV() {
    const header = "Asset,Direction,Entry Price,Exit Price,Size,Capital,P&L,Return %,Opened,Closed\n";
    const rows = filtered
      .map(
        (t) =>
          [t.asset, t.direction, t.entryPrice, t.exitPrice, t.size, t.capitalAllocated, t.pnl.toFixed(2), t.pnlPercent.toFixed(2), t.openedAt, t.closedAt]
            .map(csvEscape)
            .join(",")
      )
      .join("\n");
    const blob = new Blob([header + rows], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `jarvis-journal-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // Group trades by asset for breakdown
  const byAsset = useMemo(() => {
    const map: Record<string, { trades: number; pnl: number; wins: number }> = {};
    for (const t of allTrades) {
      if (!map[t.asset]) map[t.asset] = { trades: 0, pnl: 0, wins: 0 };
      map[t.asset].trades++;
      map[t.asset].pnl += t.pnl;
      if (t.pnl > 0) map[t.asset].wins++;
    }
    return Object.entries(map).sort((a, b) => b[1].pnl - a[1].pnl);
  }, [allTrades]);

  return (
    <>
      <AppHeader title="Trade Journal" subtitle="History & Analytics" />
      <div className="p-3 sm:p-4 md:p-6 space-y-4 md:space-y-6">
        {allTrades.length === 0 ? (
          <Card className="bg-card/50 border-border/50">
            <CardContent className="py-12 text-center">
              <BookOpen className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
              <div className="text-sm text-muted-foreground">
                No trades yet. Accept signals to start building your journal.
              </div>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Overview Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
              <Card className="bg-card/50 border-border/50">
                <CardContent className="pt-3 pb-2 px-3">
                  <div className="text-[10px] text-muted-foreground mb-0.5">Total Trades</div>
                  <div className="text-lg font-bold font-mono text-white">{allTrades.length}</div>
                </CardContent>
              </Card>
              <Card className="bg-card/50 border-border/50">
                <CardContent className="pt-3 pb-2 px-3">
                  <div className="text-[10px] text-muted-foreground mb-0.5">Win Rate</div>
                  <div className={`text-lg font-bold font-mono ${winRate >= 50 ? "text-green-400" : "text-red-400"}`}>
                    {winRate.toFixed(1)}%
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-card/50 border-border/50">
                <CardContent className="pt-3 pb-2 px-3">
                  <div className="text-[10px] text-muted-foreground mb-0.5">Total P&L</div>
                  <div className={`text-lg font-bold font-mono ${state.realizedPnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                    {state.realizedPnl >= 0 ? "+" : ""}${Math.abs(state.realizedPnl).toFixed(0)}
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-card/50 border-border/50">
                <CardContent className="pt-3 pb-2 px-3">
                  <div className="text-[10px] text-muted-foreground mb-0.5">Avg Win</div>
                  <div className="text-lg font-bold font-mono text-green-400">+${avgWin.toFixed(0)}</div>
                </CardContent>
              </Card>
              <Card className="bg-card/50 border-border/50">
                <CardContent className="pt-3 pb-2 px-3">
                  <div className="text-[10px] text-muted-foreground mb-0.5">Avg Loss</div>
                  <div className="text-lg font-bold font-mono text-red-400">${avgLoss.toFixed(0)}</div>
                </CardContent>
              </Card>
              <Card className="bg-card/50 border-border/50">
                <CardContent className="pt-3 pb-2 px-3">
                  <div className="text-[10px] text-muted-foreground mb-0.5">Profit Factor</div>
                  <div className="text-lg font-bold font-mono text-white">
                    {stats?.profitFactor === Infinity ? "∞" : (stats?.profitFactor ?? 0).toFixed(2)}
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-card/50 border-border/50">
                <CardContent className="pt-3 pb-2 px-3">
                  <div className="text-[10px] text-muted-foreground mb-0.5">Max DD</div>
                  <div className={`text-lg font-bold font-mono ${drawdown > 5 ? "text-red-400" : "text-yellow-400"}`}>
                    {drawdown.toFixed(1)}%
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-card/50 border-border/50">
                <CardContent className="pt-3 pb-2 px-3">
                  <div className="text-[10px] text-muted-foreground mb-0.5">Avg Hold</div>
                  <div className="text-lg font-bold font-mono text-white">
                    {stats ? formatDuration(stats.avgHoldTimeMs) : "—"}
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-card/50 border-border/50">
                <CardContent className="pt-3 pb-2 px-3">
                  <div className="text-[10px] text-muted-foreground mb-0.5">Noted Trades</div>
                  <div className="text-lg font-bold font-mono text-blue-400">
                    {notedTradesCount}/{allTrades.length}
                  </div>
                </CardContent>
              </Card>
            </div>

            <Tabs defaultValue="trades">
              <TabsList>
                <TabsTrigger value="trades" className="gap-1">
                  <BookOpen className="h-3 w-3" /> Trades
                </TabsTrigger>
                <TabsTrigger value="breakdown" className="gap-1">
                  <BarChart3 className="h-3 w-3" /> Breakdown
                </TabsTrigger>
              </TabsList>

              <TabsContent value="trades">
                {/* Filters */}
                <Card className="bg-card/50 border-border/50 mt-4">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between flex-wrap gap-2">
                      <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                        <Filter className="h-4 w-4" />
                        Trades ({filtered.length})
                      </CardTitle>
                      <div className="flex items-center gap-2 flex-wrap">
                        {/* Asset filter */}
                        <select
                          value={filterAsset}
                          onChange={(e) => setFilterAsset(e.target.value)}
                          className="h-7 rounded-md border border-border/50 bg-background px-2 text-xs text-white"
                        >
                          <option value="ALL">All Assets</option>
                          {tradeAssets.map((a) => (
                            <option key={a} value={a}>{a}</option>
                          ))}
                        </select>
                        {/* Direction filter */}
                        <select
                          value={filterDirection}
                          onChange={(e) => setFilterDirection(e.target.value as FilterDirection)}
                          className="h-7 rounded-md border border-border/50 bg-background px-2 text-xs text-white"
                        >
                          <option value="ALL">All Directions</option>
                          <option value="LONG">Long</option>
                          <option value="SHORT">Short</option>
                        </select>
                        {/* Result filter */}
                        <select
                          value={filterResult}
                          onChange={(e) => setFilterResult(e.target.value as FilterResult)}
                          className="h-7 rounded-md border border-border/50 bg-background px-2 text-xs text-white"
                        >
                          <option value="ALL">All Results</option>
                          <option value="WIN">Wins Only</option>
                          <option value="LOSS">Losses Only</option>
                        </select>
                        {/* Tag filter */}
                        <select
                          value={filterTag}
                          onChange={(e) => setFilterTag(e.target.value)}
                          className="h-7 rounded-md border border-border/50 bg-background px-2 text-xs text-white"
                        >
                          <option value="ALL">All Tags</option>
                          {TAG_SUGGESTIONS.map((tag) => (
                            <option key={tag} value={tag}>{tag}</option>
                          ))}
                        </select>
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-7 text-xs gap-1"
                          onClick={exportCSV}
                          disabled={filtered.length === 0}
                        >
                          <Download className="h-3 w-3" />
                          CSV
                        </Button>
                      </div>
                    </div>
                  </CardHeader>

                  {/* Filtered stats bar */}
                  {stats && (
                    <div className="px-6 pb-3 flex items-center gap-4 text-[10px] text-muted-foreground flex-wrap">
                      <span className="flex items-center gap-1">
                        <Target className="h-3 w-3" />
                        Win Rate: <span className={stats.winRate >= 50 ? "text-green-400" : "text-red-400"}>{stats.winRate.toFixed(0)}%</span>
                      </span>
                      <span className="flex items-center gap-1">
                        <DollarSign className="h-3 w-3" />
                        P&L: <span className={stats.totalPnl >= 0 ? "text-green-400" : "text-red-400"}>
                          {stats.totalPnl >= 0 ? "+" : ""}${stats.totalPnl.toFixed(2)}
                        </span>
                      </span>
                      <span className="flex items-center gap-1">
                        <TrendingUp className="h-3 w-3" />
                        Best: <span className="text-green-400">+${stats.bestTrade.toFixed(2)}</span>
                      </span>
                      <span className="flex items-center gap-1">
                        <TrendingDown className="h-3 w-3" />
                        Worst: <span className="text-red-400">${stats.worstTrade.toFixed(2)}</span>
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        Avg Hold: {formatDuration(stats.avgHoldTimeMs)}
                      </span>
                    </div>
                  )}

                  <CardContent>
                    <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-8">#</TableHead>
                          <TableHead>Asset</TableHead>
                          <TableHead>Side</TableHead>
                          <TableHead className="text-right">Entry</TableHead>
                          <TableHead className="text-right">Exit</TableHead>
                          <TableHead className="text-right">Size</TableHead>
                          <TableHead className="text-right">P&L</TableHead>
                          <TableHead className="text-right">Return</TableHead>
                          <TableHead>Duration</TableHead>
                          <TableHead>Closed</TableHead>
                          <TableHead className="text-center">Rating</TableHead>
                          <TableHead>Note</TableHead>
                          <TableHead className="w-8"></TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filtered.length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={13} className="text-center text-muted-foreground py-8">
                              No trades match filters
                            </TableCell>
                          </TableRow>
                        ) : (
                          filtered.map((trade, idx) => {
                            const duration = new Date(trade.closedAt).getTime() - new Date(trade.openedAt).getTime();
                            const tradeNote = notes[trade.id];
                            const isEditing = editingTradeId === trade.id;
                            return (
                              <React.Fragment key={trade.id + trade.closedAt}>
                                <TableRow className={isEditing ? "border-b-0" : ""}>
                                  <TableCell className="text-xs text-muted-foreground font-mono">
                                    {idx + 1}
                                  </TableCell>
                                  <TableCell className="font-medium text-white">
                                    {trade.asset}
                                  </TableCell>
                                  <TableCell>
                                    <Badge
                                      className={
                                        trade.direction === "LONG"
                                          ? "bg-green-500/20 text-green-400 border-green-500/30"
                                          : "bg-red-500/20 text-red-400 border-red-500/30"
                                      }
                                    >
                                      {trade.direction}
                                    </Badge>
                                  </TableCell>
                                  <TableCell className="text-right font-mono text-muted-foreground text-xs">
                                    ${trade.entryPrice.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                  </TableCell>
                                  <TableCell className="text-right font-mono text-white text-xs">
                                    ${trade.exitPrice.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                  </TableCell>
                                  <TableCell className="text-right font-mono text-muted-foreground text-xs">
                                    {trade.size.toFixed(4)}
                                  </TableCell>
                                  <TableCell
                                    className={`text-right font-mono ${
                                      trade.pnl >= 0 ? "text-green-400" : "text-red-400"
                                    }`}
                                  >
                                    {trade.pnl >= 0 ? "+" : ""}${Math.abs(trade.pnl).toFixed(2)}
                                  </TableCell>
                                  <TableCell
                                    className={`text-right font-mono text-xs ${
                                      trade.pnlPercent >= 0 ? "text-green-400" : "text-red-400"
                                    }`}
                                  >
                                    {trade.pnlPercent >= 0 ? "+" : ""}{trade.pnlPercent.toFixed(2)}%
                                  </TableCell>
                                  <TableCell className="text-xs text-muted-foreground font-mono">
                                    {formatDuration(duration)}
                                  </TableCell>
                                  <TableCell className="text-xs text-muted-foreground">
                                    {new Date(trade.closedAt).toLocaleDateString("en-US", {
                                      month: "short",
                                      day: "numeric",
                                      hour: "2-digit",
                                      minute: "2-digit",
                                    })}
                                  </TableCell>
                                  <TableCell className="text-center">
                                    {tradeNote && tradeNote.rating > 0 ? (
                                      <div className="flex items-center justify-center gap-0.5">
                                        {[1, 2, 3, 4, 5].map((s) => (
                                          <Star
                                            key={s}
                                            className={`h-3 w-3 ${
                                              s <= tradeNote.rating
                                                ? "fill-yellow-400 text-yellow-400"
                                                : "text-muted-foreground/30"
                                            }`}
                                          />
                                        ))}
                                      </div>
                                    ) : (
                                      <span className="text-muted-foreground/30 text-xs">--</span>
                                    )}
                                  </TableCell>
                                  <TableCell className="text-xs text-muted-foreground max-w-[150px] truncate">
                                    {tradeNote?.note ? (
                                      <span className="text-white/60" title={tradeNote.note}>
                                        {tradeNote.note.length > 30
                                          ? tradeNote.note.slice(0, 30) + "..."
                                          : tradeNote.note}
                                      </span>
                                    ) : null}
                                  </TableCell>
                                  <TableCell>
                                    <button
                                      onClick={() =>
                                        setEditingTradeId(isEditing ? null : trade.id)
                                      }
                                      className="relative p-1 rounded hover:bg-muted/30 transition-colors"
                                      title={tradeNote ? "Edit note" : "Add note"}
                                    >
                                      <StickyNote className={`h-3.5 w-3.5 ${isEditing ? "text-blue-400" : "text-muted-foreground"}`} />
                                      {tradeNote && (
                                        <span className="absolute -top-0.5 -right-0.5 h-1.5 w-1.5 rounded-full bg-blue-400" />
                                      )}
                                    </button>
                                  </TableCell>
                                </TableRow>
                                {isEditing && (
                                  <TableRow>
                                    <TableCell colSpan={13} className="p-2">
                                      <TradeNoteEditor
                                        tradeId={trade.id}
                                        onClose={() => setEditingTradeId(null)}
                                      />
                                    </TableCell>
                                  </TableRow>
                                )}
                              </React.Fragment>
                            );
                          })
                        )}
                      </TableBody>
                    </Table>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="breakdown">
                <Card className="bg-card/50 border-border/50 mt-4">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                      <BarChart3 className="h-4 w-4" />
                      Performance by Asset
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {byAsset.map(([asset, data]) => {
                        const wr = data.trades > 0 ? (data.wins / data.trades) * 100 : 0;
                        const maxPnl = Math.max(...byAsset.map(([, d]) => Math.abs(d.pnl)), 1);
                        const barWidth = (Math.abs(data.pnl) / maxPnl) * 100;

                        return (
                          <div key={asset} className="flex items-center gap-3">
                            <div className="w-12 font-bold text-white text-sm">{asset}</div>
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <div className="flex-1 h-2 rounded-full bg-background/50 overflow-hidden">
                                  <div
                                    className={`h-full rounded-full ${data.pnl >= 0 ? "bg-green-500" : "bg-red-500"}`}
                                    style={{ width: `${barWidth}%` }}
                                  />
                                </div>
                                <span className={`text-xs font-mono w-20 text-right ${data.pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                                  {data.pnl >= 0 ? "+" : ""}${data.pnl.toFixed(0)}
                                </span>
                              </div>
                              <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
                                <span>{data.trades} trades</span>
                                <span className={wr >= 50 ? "text-green-400" : "text-red-400"}>
                                  {wr.toFixed(0)}% win
                                </span>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                      {byAsset.length === 0 && (
                        <div className="text-center text-sm text-muted-foreground py-8">
                          No trades to analyze
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>

            {/* Advanced Trade Statistics */}
            <TradeStatsDashboard closedTrades={state.closedTrades} />
          </>
        )}
      </div>
    </>
  );
}
