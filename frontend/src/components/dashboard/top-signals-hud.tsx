// =============================================================================
// src/components/dashboard/top-signals-hud.tsx — Compact signal cards (right col)
// =============================================================================

"use client";

import { HudPanel } from "@/components/ui/hud-panel";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Radio, Check } from "lucide-react";
import type { Signal, PortfolioState } from "@/lib/types";

interface TopSignalsHudProps {
  signals: Signal[];
  portfolio: PortfolioState;
  acceptSignal: (signal: Signal) => void;
  loading: boolean;
}

export function TopSignalsHud({
  signals,
  portfolio,
  acceptSignal,
  loading,
}: TopSignalsHudProps) {
  const topSignals = [...signals]
    .sort((a, b) => b.confidence - a.confidence)
    .slice(0, 4);

  return (
    <HudPanel title="Top Signals" scanLine>
      <div className="p-2 space-y-2">
        {loading && topSignals.length === 0 ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="rounded bg-hud-bg/50 p-2 animate-pulse h-20" />
            ))}
          </div>
        ) : topSignals.length === 0 ? (
          <div className="text-[10px] text-muted-foreground text-center py-6">
            No signals
          </div>
        ) : (
          topSignals.map((signal) => {
            const alreadyOpen = portfolio.positions.some(
              (p) => p.asset === signal.asset && p.direction === signal.direction
            );
            return (
              <div
                key={signal.id}
                className="rounded bg-hud-bg/60 border border-hud-border/50 p-2 space-y-1.5"
              >
                {/* Header: Asset + Direction */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <span className="font-mono text-xs font-bold text-white">
                      {signal.asset}
                    </span>
                    <Badge
                      className={`text-[8px] px-1 py-0 ${
                        signal.direction === "LONG"
                          ? "bg-hud-green/20 text-hud-green border-hud-green/30"
                          : "bg-hud-red/20 text-hud-red border-hud-red/30"
                      }`}
                    >
                      {signal.direction}
                    </Badge>
                  </div>
                  <span className="font-mono text-[10px] text-hud-cyan">
                    {(signal.confidence * 100).toFixed(0)}%
                  </span>
                </div>

                {/* Entry / SL / TP from backend */}
                <div className="grid grid-cols-3 gap-1 text-[9px] font-mono">
                  <div>
                    <span className="text-muted-foreground/60">Entry</span>
                    <div className="text-white">
                      ${signal.entry.toLocaleString("en-US", { maximumFractionDigits: 0 })}
                    </div>
                  </div>
                  <div>
                    <span className="text-hud-red/60">SL</span>
                    <div className="text-hud-red">
                      ${signal.stopLoss.toLocaleString("en-US", { maximumFractionDigits: 0 })}
                    </div>
                  </div>
                  <div>
                    <span className="text-hud-green/60">TP</span>
                    <div className="text-hud-green">
                      ${signal.takeProfit.toLocaleString("en-US", { maximumFractionDigits: 0 })}
                    </div>
                  </div>
                </div>

                {/* Confidence bar */}
                <Progress
                  value={signal.confidence * 100}
                  className="h-1"
                  indicatorClassName={
                    signal.confidence > 0.7
                      ? "bg-hud-green"
                      : signal.confidence > 0.4
                        ? "bg-hud-amber"
                        : "bg-hud-red"
                  }
                />

                {/* Trade button */}
                <button
                  onClick={() => {
                    if (!alreadyOpen) acceptSignal(signal);
                  }}
                  disabled={alreadyOpen}
                  className={`w-full py-1 rounded text-[9px] font-mono uppercase tracking-wider transition-colors ${
                    alreadyOpen
                      ? "text-hud-green/50 border border-hud-green/20 cursor-default"
                      : "bg-hud-cyan/10 text-hud-cyan border border-hud-cyan/30 hover:bg-hud-cyan/20"
                  }`}
                  suppressHydrationWarning
                >
                  <span className="flex items-center justify-center gap-1" suppressHydrationWarning>
                    {alreadyOpen && <Check className="h-3 w-3" />}
                    {alreadyOpen ? "OPEN" : "TRADE"}
                  </span>
                </button>
              </div>
            );
          })
        )}

        {/* Signal count */}
        <div className="flex items-center justify-center gap-1 pt-1 text-[9px] font-mono text-muted-foreground/50">
          <Radio className="h-2.5 w-2.5" />
          {signals.length} active
        </div>
      </div>
    </HudPanel>
  );
}
