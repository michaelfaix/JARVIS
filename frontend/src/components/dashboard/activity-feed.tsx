// =============================================================================
// src/components/dashboard/activity-feed.tsx — Recent trading activity feed
// =============================================================================

"use client";

import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  TrendingUp,
  TrendingDown,
  ArrowRightCircle,
  Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ActivityFeedProps {
  closedTrades: Array<{
    id: string;
    asset: string;
    direction: "LONG" | "SHORT";
    pnl: number;
    closedAt: string;
  }>;
  openPositions: Array<{
    asset: string;
    direction: "LONG" | "SHORT";
    openedAt: string;
  }>;
}

interface ActivityItem {
  key: string;
  icon: React.ReactNode;
  title: string;
  description: string;
  time: Date;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function relativeTime(date: Date): string {
  const now = Date.now();
  const diffMs = now - date.getTime();
  if (diffMs < 0) return "just now";

  const seconds = Math.floor(diffMs / 1000);
  if (seconds < 60) return "just now";

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;

  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function formatPnl(pnl: number): string {
  const sign = pnl >= 0 ? "+" : "";
  return `${sign}$${Math.abs(pnl).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ActivityFeed({ closedTrades, openPositions }: ActivityFeedProps) {
  const activities = useMemo<ActivityItem[]>(() => {
    const items: ActivityItem[] = [];

    for (const trade of closedTrades) {
      const profitable = trade.pnl >= 0;
      items.push({
        key: `closed-${trade.id}`,
        icon: profitable ? (
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-green-500/15">
            <TrendingUp className="h-3.5 w-3.5 text-green-400" />
          </div>
        ) : (
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-red-500/15">
            <TrendingDown className="h-3.5 w-3.5 text-red-400" />
          </div>
        ),
        title: `Closed ${trade.asset} ${trade.direction}`,
        description: `P&L: ${formatPnl(trade.pnl)}`,
        time: new Date(trade.closedAt),
      });
    }

    for (const pos of openPositions) {
      items.push({
        key: `opened-${pos.asset}-${pos.openedAt}`,
        icon: (
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-blue-500/15">
            <ArrowRightCircle className="h-3.5 w-3.5 text-blue-400" />
          </div>
        ),
        title: `Opened ${pos.asset} ${pos.direction}`,
        description: `${pos.direction === "LONG" ? "Buying" : "Selling"} ${pos.asset}`,
        time: new Date(pos.openedAt),
      });
    }

    items.sort((a, b) => b.time.getTime() - a.time.getTime());
    return items.slice(0, 10);
  }, [closedTrades, openPositions]);

  return (
    <Card className="bg-card/50 border-border/50">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          <Activity className="h-4 w-4" />
          Recent Activity
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-1">
        {activities.length === 0 ? (
          <div className="text-xs text-muted-foreground text-center py-4">
            No recent activity
          </div>
        ) : (
          activities.map((item) => (
            <div
              key={item.key}
              className="flex items-center gap-3 rounded-lg bg-background/50 px-3 py-2"
            >
              {item.icon}
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-white truncate">
                  {item.title}
                </div>
                <div
                  className={cn(
                    "text-xs truncate",
                    item.description.includes("+")
                      ? "text-green-400"
                      : item.description.startsWith("P&L: -")
                      ? "text-red-400"
                      : "text-muted-foreground"
                  )}
                >
                  {item.description}
                </div>
              </div>
              <span className="text-[10px] text-muted-foreground whitespace-nowrap shrink-0">
                {relativeTime(item.time)}
              </span>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
