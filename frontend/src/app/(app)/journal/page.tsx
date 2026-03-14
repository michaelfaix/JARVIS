// =============================================================================
// src/app/(app)/journal/page.tsx — Trade Journal with filtering & analytics
// =============================================================================

"use client";

import React, { useMemo, useState } from "react";
import { HudPanel } from "@/components/ui/hud-panel";
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
import { useLocale } from "@/hooks/use-locale";
import { TradeNoteEditor } from "@/components/journal/trade-note-editor";
import { TradeStatsDashboard } from "@/components/portfolio/trade-stats-dashboard";
import {
  generateTradeReview,
  type CoPilotContext,
  type RiskProfile,
} from "@/lib/copilot-engine";
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
  BrainCircuit,
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
  const [reviewTradeId, setReviewTradeId] = useState<string | null>(null);
  const { locale } = useLocale();

  // Default CoPilotContext for KI Trade Review (uses portfolio-level stats)
  const defaultCtx: CoPilotContext = useMemo(() => ({
    regime: "RISK_ON",
    ece: 0.03,
    oodScore: 0.2,
    metaUncertainty: 0.1,
    strategy: "momentum",
    selectedAsset: "",
    interval: "1d",
    slPercent: 3,
    tpPercent: 6,
    currentPrice: 0,
    totalValue: state.totalCapital + state.realizedPnl,
    drawdown: drawdown,
    positionCount: state.positions.length,
    closedTradeCount: state.closedTrades.length,
    realizedPnl: state.realizedPnl,
    winRate: winRate,
    signalCount: 0,
    topSignalAsset: null,
    topSignalDirection: null,
    topSignalConfidence: 0.7,
    patterns: [],
  }), [state, drawdown, winRate]);

  const riskProfile: RiskProfile = "moderate";

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
    let s = String(val);
    // Prevent CSV formula injection — prefix dangerous leading chars with a tab
    if (/^[=+\-@\t\r]/.test(s)) {
      s = "\t" + s;
    }
    return '"' + s.replace(/"/g, '""') + '"';
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
    <div className="p-2 sm:p-3 md:p-4 space-y-3">
      {allTrades.length === 0 ? (
        <HudPanel title="TRADE JOURNAL">
          <div className="py-12 text-center">
            <BookOpen className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
            <div className="text-sm text-muted-foreground">
              No trades yet. Accept signals to start building your journal.
            </div>
          </div>
        </HudPanel>
      ) : (
        <>
          {/* Overview Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
            <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
              <div className="text-[10px] text-muted-foreground mb-0.5">TOTAL TRADES</div>
              <div className="text-lg font-bold font-mono text-white">{allTrades.length}</div>
            </div>
            <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
              <div className="text-[10px] text-muted-foreground mb-0.5">WIN RATE</div>
              <div className={`text-lg font-bold font-mono ${winRate >= 50 ? "text-hud-green" : "text-hud-red"}`}>
                {winRate.toFixed(1)}%
              </div>
            </div>
            <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
              <div className="text-[10px] text-muted-foreground mb-0.5">TOTAL P&L</div>
              <div className={`text-lg font-bold font-mono ${state.realizedPnl >= 0 ? "text-hud-green" : "text-hud-red"}`}>
                {state.realizedPnl >= 0 ? "+" : ""}${Math.abs(state.realizedPnl).toFixed(0)}
              </div>
            </div>
            <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
              <div className="text-[10px] text-muted-foreground mb-0.5">AVG WIN</div>
              <div className="text-lg font-bold font-mono text-hud-green">+${avgWin.toFixed(0)}</div>
            </div>
            <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
              <div className="text-[10px] text-muted-foreground mb-0.5">AVG LOSS</div>
              <div className="text-lg font-bold font-mono text-hud-red">${avgLoss.toFixed(0)}</div>
            </div>
            <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
              <div className="text-[10px] text-muted-foreground mb-0.5">PROFIT FACTOR</div>
              <div className="text-lg font-bold font-mono text-white">
                {stats?.profitFactor === Infinity ? "∞" : (stats?.profitFactor ?? 0).toFixed(2)}
              </div>
            </div>
            <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
              <div className="text-[10px] text-muted-foreground mb-0.5">MAX DD</div>
              <div className={`text-lg font-bold font-mono ${drawdown > 5 ? "text-hud-red" : "text-hud-amber"}`}>
                {drawdown.toFixed(1)}%
              </div>
            </div>
            <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
              <div className="text-[10px] text-muted-foreground mb-0.5">AVG HOLD</div>
              <div className="text-lg font-bold font-mono text-white">
                {stats ? formatDuration(stats.avgHoldTimeMs) : "—"}
              </div>
            </div>
            <div className="bg-hud-bg/60 border border-hud-border/30 rounded p-2.5">
              <div className="text-[10px] text-muted-foreground mb-0.5">NOTED TRADES</div>
              <div className="text-lg font-bold font-mono text-hud-cyan">
                {notedTradesCount}/{allTrades.length}
              </div>
            </div>
          </div>

          <Tabs defaultValue="trades">
            <TabsList className="bg-hud-bg/60 border border-hud-border/30">
              <TabsTrigger value="trades" className="gap-1 data-[state=active]:text-hud-cyan">
                <BookOpen className="h-3 w-3" /> Trades
              </TabsTrigger>
              <TabsTrigger value="breakdown" className="gap-1 data-[state=active]:text-hud-cyan">
                <BarChart3 className="h-3 w-3" /> Breakdown
              </TabsTrigger>
            </TabsList>

            <TabsContent value="trades">
              {/* Filters */}
              <HudPanel title="TRADE LOG" className="mt-4">
                <div className="p-2 sm:p-3 md:p-4">
                  <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
                    <div className="text-[10px] text-muted-foreground flex items-center gap-2 font-mono">
                      <Filter className="h-4 w-4" />
                      TRADES ({filtered.length})
                    </div>
                    <div className="flex items-center gap-2 flex-wrap">
                      {/* Asset filter */}
                      <select
                        value={filterAsset}
                        onChange={(e) => setFilterAsset(e.target.value)}
                        className="h-7 rounded-md border border-hud-border/50 bg-hud-bg/60 px-2 text-xs text-white font-mono"
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
                        className="h-7 rounded-md border border-hud-border/50 bg-hud-bg/60 px-2 text-xs text-white font-mono"
                      >
                        <option value="ALL">All Directions</option>
                        <option value="LONG">Long</option>
                        <option value="SHORT">Short</option>
                      </select>
                      {/* Result filter */}
                      <select
                        value={filterResult}
                        onChange={(e) => setFilterResult(e.target.value as FilterResult)}
                        className="h-7 rounded-md border border-hud-border/50 bg-hud-bg/60 px-2 text-xs text-white font-mono"
                      >
                        <option value="ALL">All Results</option>
                        <option value="WIN">Wins Only</option>
                        <option value="LOSS">Losses Only</option>
                      </select>
                      {/* Tag filter */}
                      <select
                        value={filterTag}
                        onChange={(e) => setFilterTag(e.target.value)}
                        className="h-7 rounded-md border border-hud-border/50 bg-hud-bg/60 px-2 text-xs text-white font-mono"
                      >
                        <option value="ALL">All Tags</option>
                        {TAG_SUGGESTIONS.map((tag) => (
                          <option key={tag} value={tag}>{tag}</option>
                        ))}
                      </select>
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-7 text-xs gap-1 border-hud-border/50 text-hud-cyan hover:bg-hud-cyan/10"
                        onClick={exportCSV}
                        disabled={filtered.length === 0}
                      >
                        <Download className="h-3 w-3" />
                        CSV
                      </Button>
                    </div>
                  </div>

                  {/* Filtered stats bar */}
                  {stats && (
                    <div className="pb-3 flex items-center gap-4 text-[10px] text-muted-foreground flex-wrap font-mono">
                      <span className="flex items-center gap-1">
                        <Target className="h-3 w-3" />
                        Win Rate: <span className={stats.winRate >= 50 ? "text-hud-green" : "text-hud-red"}>{stats.winRate.toFixed(0)}%</span>
                      </span>
                      <span className="flex items-center gap-1">
                        <DollarSign className="h-3 w-3" />
                        P&L: <span className={stats.totalPnl >= 0 ? "text-hud-green" : "text-hud-red"}>
                          {stats.totalPnl >= 0 ? "+" : ""}${stats.totalPnl.toFixed(2)}
                        </span>
                      </span>
                      <span className="flex items-center gap-1">
                        <TrendingUp className="h-3 w-3" />
                        Best: <span className="text-hud-green">+${stats.bestTrade.toFixed(2)}</span>
                      </span>
                      <span className="flex items-center gap-1">
                        <TrendingDown className="h-3 w-3" />
                        Worst: <span className="text-hud-red">${stats.worstTrade.toFixed(2)}</span>
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        Avg Hold: {formatDuration(stats.avgHoldTimeMs)}
                      </span>
                    </div>
                  )}

                  <div className="overflow-x-auto">
                    <Table className="border-hud-border/30">
                      <TableHeader>
                        <TableRow className="border-hud-border/30">
                          <TableHead className="w-8 text-[10px] font-mono">#</TableHead>
                          <TableHead className="text-[10px] font-mono">Asset</TableHead>
                          <TableHead className="text-[10px] font-mono">Side</TableHead>
                          <TableHead className="text-right text-[10px] font-mono">Entry</TableHead>
                          <TableHead className="text-right text-[10px] font-mono">Exit</TableHead>
                          <TableHead className="text-right text-[10px] font-mono">Size</TableHead>
                          <TableHead className="text-right text-[10px] font-mono">P&L</TableHead>
                          <TableHead className="text-right text-[10px] font-mono">Return</TableHead>
                          <TableHead className="text-[10px] font-mono">Duration</TableHead>
                          <TableHead className="text-[10px] font-mono">Closed</TableHead>
                          <TableHead className="text-center text-[10px] font-mono">Rating</TableHead>
                          <TableHead className="text-[10px] font-mono">Note</TableHead>
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
                                <TableRow className={`border-hud-border/30 ${isEditing ? "border-b-0" : ""}`}>
                                  <TableCell className="text-xs text-muted-foreground font-mono">
                                    {idx + 1}
                                  </TableCell>
                                  <TableCell className="font-medium text-white font-mono">
                                    {trade.asset}
                                  </TableCell>
                                  <TableCell>
                                    <Badge
                                      className={
                                        trade.direction === "LONG"
                                          ? "bg-hud-green/20 text-hud-green border-hud-green/30"
                                          : "bg-hud-red/20 text-hud-red border-hud-red/30"
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
                                      trade.pnl >= 0 ? "text-hud-green" : "text-hud-red"
                                    }`}
                                  >
                                    {trade.pnl >= 0 ? "+" : ""}${Math.abs(trade.pnl).toFixed(2)}
                                  </TableCell>
                                  <TableCell
                                    className={`text-right font-mono text-xs ${
                                      trade.pnlPercent >= 0 ? "text-hud-green" : "text-hud-red"
                                    }`}
                                  >
                                    {trade.pnlPercent >= 0 ? "+" : ""}{trade.pnlPercent.toFixed(2)}%
                                  </TableCell>
                                  <TableCell className="text-xs text-muted-foreground font-mono">
                                    {formatDuration(duration)}
                                  </TableCell>
                                  <TableCell className="text-xs text-muted-foreground font-mono">
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
                                                ? "fill-hud-amber text-hud-amber"
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
                                    <div className="flex items-center gap-1">
                                      <button
                                        onClick={() =>
                                          setReviewTradeId(reviewTradeId === trade.id ? null : trade.id)
                                        }
                                        className="relative p-1 rounded hover:bg-hud-amber/10 transition-colors"
                                        title="KI Review"
                                      >
                                        <BrainCircuit className={`h-3.5 w-3.5 ${reviewTradeId === trade.id ? "text-hud-amber" : "text-muted-foreground"}`} />
                                      </button>
                                      <button
                                        onClick={() =>
                                          setEditingTradeId(isEditing ? null : trade.id)
                                        }
                                        className="relative p-1 rounded hover:bg-hud-cyan/10 transition-colors"
                                        title={tradeNote ? "Edit note" : "Add note"}
                                      >
                                        <StickyNote className={`h-3.5 w-3.5 ${isEditing ? "text-hud-cyan" : "text-muted-foreground"}`} />
                                        {tradeNote && (
                                          <span className="absolute -top-0.5 -right-0.5 h-1.5 w-1.5 rounded-full bg-hud-cyan" />
                                        )}
                                      </button>
                                    </div>
                                  </TableCell>
                                </TableRow>
                                {reviewTradeId === trade.id && (
                                  <TableRow>
                                    <TableCell colSpan={13} className="p-3">
                                      <div className="bg-hud-bg/80 border border-hud-border/40 rounded-lg p-4 text-sm text-white/80 whitespace-pre-line font-mono leading-relaxed">
                                        <div className="flex items-center gap-2 mb-2 text-xs text-hud-amber font-semibold uppercase tracking-wider">
                                          <BrainCircuit className="h-4 w-4" />
                                          KI-Coaching Trade Review
                                        </div>
                                        {generateTradeReview(
                                          {
                                            asset: trade.asset,
                                            direction: trade.direction,
                                            entryPrice: trade.entryPrice,
                                            exitPrice: trade.exitPrice,
                                            pnl: trade.pnl,
                                            pnlPercent: trade.pnlPercent,
                                            holdingPeriod: formatDuration(
                                              new Date(trade.closedAt).getTime() - new Date(trade.openedAt).getTime()
                                            ),
                                          },
                                          defaultCtx,
                                          locale === "de" ? "de" : "en",
                                          riskProfile
                                        )}
                                      </div>
                                    </TableCell>
                                  </TableRow>
                                )}
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
                </div>
              </HudPanel>
            </TabsContent>

            <TabsContent value="breakdown">
              <HudPanel title="PERFORMANCE BY ASSET" className="mt-4">
                <div className="p-2 sm:p-3 md:p-4">
                  <div className="space-y-3">
                    {byAsset.map(([asset, data]) => {
                      const wr = data.trades > 0 ? (data.wins / data.trades) * 100 : 0;
                      const maxPnl = Math.max(...byAsset.map(([, d]) => Math.abs(d.pnl)), 1);
                      const barWidth = (Math.abs(data.pnl) / maxPnl) * 100;

                      return (
                        <div key={asset} className="flex items-center gap-3">
                          <div className="w-12 font-bold text-white text-sm font-mono">{asset}</div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <div className="flex-1 h-2 rounded-full bg-hud-bg/60 overflow-hidden">
                                <div
                                  className={`h-full rounded-full ${data.pnl >= 0 ? "bg-hud-green" : "bg-hud-red"}`}
                                  style={{ width: `${barWidth}%` }}
                                />
                              </div>
                              <span className={`text-xs font-mono w-20 text-right ${data.pnl >= 0 ? "text-hud-green" : "text-hud-red"}`}>
                                {data.pnl >= 0 ? "+" : ""}${data.pnl.toFixed(0)}
                              </span>
                            </div>
                            <div className="flex items-center gap-3 text-[10px] text-muted-foreground font-mono">
                              <span>{data.trades} trades</span>
                              <span className={wr >= 50 ? "text-hud-green" : "text-hud-red"}>
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
                </div>
              </HudPanel>
            </TabsContent>
          </Tabs>

          {/* Advanced Trade Statistics */}
          <TradeStatsDashboard closedTrades={state.closedTrades} />
        </>
      )}
    </div>
  );
}
