// =============================================================================
// src/components/social/trader-feed.tsx — Activity feed for followed traders
// =============================================================================

"use client";

import { useMemo } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useSocialTrading } from "@/hooks/use-social-trading";
import {
  Copy,
  Users,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import Link from "next/link";

interface FeedEntry {
  id: string;
  traderName: string;
  traderId: string;
  asset: string;
  direction: "LONG" | "SHORT";
  entryPrice: number;
  pnl: number;
  pnlPercent: number;
  timeAgo: string;
  status: "open" | "closed";
}

const ASSETS = ["BTC/USD", "ETH/USD", "SOL/USD", "AAPL", "TSLA", "EUR/USD", "GBP/USD", "XAU/USD"];

const TRADER_NAMES: Record<string, string> = {
  "CryptoWhale_99": "CryptoWhale_99",
  "AlgoTrader_Pro": "AlgoTrader_Pro",
  "JarvisBot_1": "JarvisBot_1",
  "MomentumKing": "MomentumKing",
  "Sven_Berlin": "Sven_Berlin",
  "TrendFollower": "TrendFollower",
  "SmartMoneyFx": "SmartMoneyFx",
  "DayTraderMax": "DayTraderMax",
  "SwingSetup_AI": "SwingSetup_AI",
  "HODLer2024": "HODLer2024",
  "ScalpMaster": "ScalpMaster",
  "NoviceTrader": "NoviceTrader",
};

function seededRandom(seed: number): number {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

function generateFeedEntries(followedTraders: string[]): FeedEntry[] {
  if (followedTraders.length === 0) return [];

  const entries: FeedEntry[] = [];
  const timeOffsets = [
    "2m ago", "5m ago", "12m ago", "18m ago", "25m ago",
    "34m ago", "45m ago", "1h ago", "1.5h ago", "2h ago",
    "2.5h ago", "3h ago", "4h ago", "5h ago", "6h ago",
    "8h ago", "10h ago", "12h ago", "18h ago", "1d ago",
  ];

  for (let i = 0; i < 20; i++) {
    const traderIdx = Math.floor(seededRandom(i * 7 + 3) * followedTraders.length);
    const traderId = followedTraders[traderIdx];
    const traderName = TRADER_NAMES[traderId] ?? traderId;
    const assetIdx = Math.floor(seededRandom(i * 13 + 5) * ASSETS.length);
    const asset = ASSETS[assetIdx];
    const direction = seededRandom(i * 17 + 11) > 0.45 ? "LONG" as const : "SHORT" as const;
    const entryPrice = asset.includes("BTC") ? 60000 + seededRandom(i * 23) * 5000 :
                       asset.includes("ETH") ? 3200 + seededRandom(i * 29) * 400 :
                       asset.includes("SOL") ? 140 + seededRandom(i * 31) * 30 :
                       asset.includes("XAU") ? 2300 + seededRandom(i * 37) * 100 :
                       100 + seededRandom(i * 41) * 200;
    const pnl = (seededRandom(i * 43 + 7) - 0.35) * 500;
    const pnlPercent = (seededRandom(i * 47 + 9) - 0.35) * 8;
    const status = seededRandom(i * 53 + 1) > 0.4 ? "closed" as const : "open" as const;

    entries.push({
      id: `feed-${i}`,
      traderName,
      traderId,
      asset,
      direction,
      entryPrice: Math.round(entryPrice * 100) / 100,
      pnl: Math.round(pnl * 100) / 100,
      pnlPercent: Math.round(pnlPercent * 100) / 100,
      timeAgo: timeOffsets[i] ?? `${i}h ago`,
      status,
    });
  }

  return entries;
}

export function TraderFeed() {
  const { followedTraders } = useSocialTrading();

  const entries = useMemo(
    () => generateFeedEntries(followedTraders),
    [followedTraders]
  );

  if (followedTraders.length === 0) {
    return (
      <Card className="bg-card/50 border-border/50">
        <CardContent className="pt-8 pb-8 px-4 text-center">
          <Users className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
          <div className="text-sm font-medium text-white mb-1">No traders followed</div>
          <div className="text-xs text-muted-foreground mb-4">
            Follow traders from the Leaderboard to see their activity
          </div>
          <Link href="/leaderboard">
            <Button variant="outline" size="sm" className="text-xs">
              Go to Leaderboard
            </Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-2">
      {entries.map((entry) => (
        <Card key={entry.id} className="bg-card/50 border-border/50">
          <CardContent className="py-2.5 px-3">
            <div className="flex items-center gap-3">
              {/* Direction Icon */}
              <div
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${
                  entry.direction === "LONG" ? "bg-green-500/10" : "bg-red-500/10"
                }`}
              >
                {entry.direction === "LONG" ? (
                  <ArrowUpRight className="h-4 w-4 text-green-400" />
                ) : (
                  <ArrowDownRight className="h-4 w-4 text-red-400" />
                )}
              </div>

              {/* Trade Info */}
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-medium text-blue-400 truncate">
                    {entry.traderName}
                  </span>
                  <span className="text-[10px] text-muted-foreground">
                    {entry.direction === "LONG" ? "bought" : "shorted"}
                  </span>
                  <span className="text-xs font-medium text-white">{entry.asset}</span>
                  <Badge
                    variant="outline"
                    className={`text-[8px] ml-1 ${
                      entry.status === "open"
                        ? "text-blue-400 border-blue-400/30"
                        : "text-muted-foreground border-border/50"
                    }`}
                  >
                    {entry.status}
                  </Badge>
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-[10px] text-muted-foreground font-mono">
                    @{entry.entryPrice.toLocaleString()}
                  </span>
                  <span
                    className={`text-[10px] font-mono font-medium ${
                      entry.pnl >= 0 ? "text-green-400" : "text-red-400"
                    }`}
                  >
                    {entry.pnl >= 0 ? "+" : ""}${entry.pnl.toFixed(2)} ({entry.pnlPercent >= 0 ? "+" : ""}{entry.pnlPercent.toFixed(2)}%)
                  </span>
                  <span className="text-[9px] text-muted-foreground">{entry.timeAgo}</span>
                </div>
              </div>

              {/* Copy Action */}
              <Button
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-[10px] text-muted-foreground hover:text-blue-400 shrink-0"
                title="Copy this trade"
              >
                <Copy className="h-3 w-3 mr-1" />
                Copy
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
