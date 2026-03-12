// =============================================================================
// src/components/dashboard/pnl-ticker.tsx — Floating P&L Ticker
//
// Compact horizontal ticker showing real-time P&L for all open positions.
// Displayed at the top of the main content area with live price updates.
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
  return `${sign}$${Math.abs(value).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function calcPnl(position: Position, currentPrice: number): number {
  return position.direction === "LONG"
    ? (currentPrice - position.entryPrice) * position.size
    : (position.entryPrice - currentPrice) * position.size;
}

export function PnlTicker({ positions, prices }: PnlTickerProps) {
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
        "bg-background/80 backdrop-blur-sm border-b border-border/30",
        "flex items-center gap-3 px-4 py-1.5",
        "overflow-x-auto scrollbar-hide"
      )}
      style={{ fontSize: "11px" }}
    >
      {/* Label */}
      <span className="text-muted-foreground whitespace-nowrap shrink-0">
        Open P&amp;L
      </span>

      {/* Position entries */}
      <div className="flex items-center gap-2 min-w-0">
        {pnlEntries.map((entry, idx) => (
          <React.Fragment key={entry.asset}>
            {idx > 0 && (
              <span className="text-muted-foreground/40 shrink-0">·</span>
            )}
            <span className="whitespace-nowrap shrink-0 flex items-center gap-1">
              <span className="text-foreground font-medium">{entry.asset}</span>
              <span
                className={cn(
                  "font-medium",
                  entry.direction === "LONG"
                    ? "text-green-400"
                    : "text-red-400"
                )}
              >
                {entry.direction === "LONG" ? "▲" : "▼"}
              </span>
              <span
                className={cn(
                  "tabular-nums",
                  entry.pnl >= 0 ? "text-green-400" : "text-red-400"
                )}
              >
                {formatPnl(entry.pnl)}
              </span>
            </span>
          </React.Fragment>
        ))}
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Total */}
      <span
        className={cn(
          "whitespace-nowrap shrink-0 font-bold tabular-nums",
          totalPnl >= 0 ? "text-green-400" : "text-red-400"
        )}
      >
        {formatPnl(totalPnl)}
      </span>
    </div>
  );
}
