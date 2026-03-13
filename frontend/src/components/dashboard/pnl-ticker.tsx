// =============================================================================
// src/components/dashboard/pnl-ticker.tsx — P&L Ticker (HUD)
// =============================================================================

"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface Position {
  asset: string;
  direction: "LONG" | "SHORT";
  entryPrice: number;
  size: number;
}

interface PnlTickerProps {
  positions: Array<Position>;
  prices: Record<string, number>;
}

function formatPnl(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}$${Math.abs(value).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function calcPnl(position: Position, currentPrice: number): number {
  return position.direction === "LONG"
    ? (currentPrice - position.entryPrice) * position.size
    : (position.entryPrice - currentPrice) * position.size;
}

export const PnlTicker = React.memo(function PnlTicker({ positions, prices }: PnlTickerProps) {
  if (!positions || positions.length === 0) return null;

  const pnlEntries = positions.map((pos) => {
    const currentPrice = prices[pos.asset] ?? pos.entryPrice;
    const pnl = calcPnl(pos, currentPrice);
    return { ...pos, pnl };
  });

  const totalPnl = pnlEntries.reduce((sum, entry) => sum + entry.pnl, 0);

  return (
    <div
      className={cn(
        "sticky top-0 z-10",
        "bg-hud-bg/90 backdrop-blur-sm border-b border-hud-border/50",
        "flex items-center gap-3 px-3 py-1",
        "overflow-x-auto scrollbar-hide"
      )}
      style={{ fontSize: "10px" }}
    >
      <span className="font-mono text-muted-foreground/60 whitespace-nowrap shrink-0 uppercase tracking-wider text-[8px]">
        Open P&amp;L
      </span>

      <div className="flex items-center gap-2 min-w-0">
        {pnlEntries.map((entry, idx) => (
          <React.Fragment key={entry.asset}>
            {idx > 0 && <span className="text-hud-border shrink-0">·</span>}
            <span className="whitespace-nowrap shrink-0 flex items-center gap-1 font-mono">
              <span className="text-white font-medium">{entry.asset}</span>
              <span className={entry.direction === "LONG" ? "text-hud-green" : "text-hud-red"}>
                {entry.direction === "LONG" ? "▲" : "▼"}
              </span>
              <span className={cn("tabular-nums", entry.pnl >= 0 ? "text-hud-green" : "text-hud-red")}>
                {formatPnl(entry.pnl)}
              </span>
            </span>
          </React.Fragment>
        ))}
      </div>

      <div className="flex-1" />

      <span className={cn("whitespace-nowrap shrink-0 font-bold font-mono tabular-nums", totalPnl >= 0 ? "text-hud-green" : "text-hud-red")}>
        {formatPnl(totalPnl)}
      </span>
    </div>
  );
});
