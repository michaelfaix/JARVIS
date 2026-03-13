// =============================================================================
// src/components/dashboard/activity-feed.tsx — Activity Feed (HUD)
// =============================================================================

"use client";

import { useMemo } from "react";
import { HudPanel } from "@/components/ui/hud-panel";
import { TrendingUp, TrendingDown, ArrowRightCircle } from "lucide-react";
import { cn } from "@/lib/utils";

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

function relativeTime(date: Date): string {
  const diffMs = Date.now() - date.getTime();
  if (diffMs < 0) return "now";
  const seconds = Math.floor(diffMs / 1000);
  if (seconds < 60) return "now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h`;
  return `${Math.floor(hours / 24)}d`;
}

function formatPnl(pnl: number): string {
  const sign = pnl >= 0 ? "+" : "";
  return `${sign}$${Math.abs(pnl).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function ActivityFeed({ closedTrades, openPositions }: ActivityFeedProps) {
  const activities = useMemo<ActivityItem[]>(() => {
    const items: ActivityItem[] = [];

    for (const trade of closedTrades) {
      const profitable = trade.pnl >= 0;
      items.push({
        key: `closed-${trade.id}`,
        icon: (
          <div className={cn("flex h-5 w-5 shrink-0 items-center justify-center rounded", profitable ? "bg-hud-green/15" : "bg-hud-red/15")}>
            {profitable ? <TrendingUp className="h-2.5 w-2.5 text-hud-green" /> : <TrendingDown className="h-2.5 w-2.5 text-hud-red" />}
          </div>
        ),
        title: `${trade.asset} ${trade.direction}`,
        description: formatPnl(trade.pnl),
        time: new Date(trade.closedAt),
      });
    }

    for (const pos of openPositions) {
      items.push({
        key: `opened-${pos.asset}-${pos.openedAt}`,
        icon: (
          <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-hud-cyan/15">
            <ArrowRightCircle className="h-2.5 w-2.5 text-hud-cyan" />
          </div>
        ),
        title: `${pos.asset} ${pos.direction}`,
        description: pos.direction === "LONG" ? "Buy" : "Sell",
        time: new Date(pos.openedAt),
      });
    }

    items.sort((a, b) => b.time.getTime() - a.time.getTime());
    return items.slice(0, 10);
  }, [closedTrades, openPositions]);

  return (
    <HudPanel title="Activity">
      <div className="p-2 space-y-0.5">
        {activities.length === 0 ? (
          <div className="text-[10px] font-mono text-muted-foreground text-center py-4">
            No activity
          </div>
        ) : (
          activities.map((item) => (
            <div key={item.key} className="flex items-center gap-2 rounded bg-hud-bg/40 px-2 py-1.5">
              {item.icon}
              <div className="flex-1 min-w-0">
                <div className="text-[10px] font-mono font-medium text-white truncate">{item.title}</div>
                <div className={cn("text-[9px] font-mono truncate", item.description.includes("+") ? "text-hud-green" : item.description.startsWith("-") ? "text-hud-red" : "text-muted-foreground")}>
                  {item.description}
                </div>
              </div>
              <span className="text-[8px] font-mono text-muted-foreground/50 shrink-0">{relativeTime(item.time)}</span>
            </div>
          ))
        )}
      </div>
    </HudPanel>
  );
}
