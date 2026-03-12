// =============================================================================
// src/app/(app)/social/page.tsx — Social Trading page
// =============================================================================

"use client";

import { useMemo } from "react";
import { AppHeader } from "@/components/layout/app-header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TraderProfileCard, type TraderData } from "@/components/social/trader-profile-card";
import { TraderFeed } from "@/components/social/trader-feed";
import { useSocialTrading } from "@/hooks/use-social-trading";
import {
  Users,
  Activity,
  Copy,
  Heart,
  TrendingUp,
  TrendingDown,
  DollarSign,
} from "lucide-react";
import Link from "next/link";

// All simulated traders (same as leaderboard)
const ALL_TRADERS: TraderData[] = [
  { id: "CryptoWhale_99", name: "CryptoWhale_99", tier: "enterprise", totalReturn: 34.2, winRate: 72, trades: 156, drawdown: 4.1 },
  { id: "AlgoTrader_Pro", name: "AlgoTrader_Pro", tier: "pro", totalReturn: 28.7, winRate: 68, trades: 243, drawdown: 5.3 },
  { id: "JarvisBot_1", name: "JarvisBot_1", tier: "enterprise", totalReturn: 24.1, winRate: 65, trades: 412, drawdown: 3.8 },
  { id: "MomentumKing", name: "MomentumKing", tier: "pro", totalReturn: 19.5, winRate: 61, trades: 89, drawdown: 7.2 },
  { id: "Sven_Berlin", name: "Sven_Berlin", tier: "pro", totalReturn: 16.8, winRate: 59, trades: 67, drawdown: 6.1 },
  { id: "TrendFollower", name: "TrendFollower", tier: "free", totalReturn: 14.3, winRate: 57, trades: 45, drawdown: 8.4 },
  { id: "SmartMoneyFx", name: "SmartMoneyFx", tier: "pro", totalReturn: 12.1, winRate: 55, trades: 112, drawdown: 5.9 },
  { id: "DayTraderMax", name: "DayTraderMax", tier: "free", totalReturn: 9.8, winRate: 53, trades: 198, drawdown: 9.1 },
  { id: "SwingSetup_AI", name: "SwingSetup_AI", tier: "pro", totalReturn: 7.4, winRate: 51, trades: 34, drawdown: 4.5 },
  { id: "HODLer2024", name: "HODLer2024", tier: "free", totalReturn: 5.2, winRate: 50, trades: 12, drawdown: 11.2 },
  { id: "ScalpMaster", name: "ScalpMaster", tier: "free", totalReturn: 3.1, winRate: 48, trades: 301, drawdown: 6.8 },
  { id: "NoviceTrader", name: "NoviceTrader", tier: "free", totalReturn: -2.4, winRate: 42, trades: 28, drawdown: 14.5 },
];

function seededRandom(seed: number): number {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

export default function SocialPage() {
  const { followedTraders, copySettings, setCopySettings, followCount, maxFollows } = useSocialTrading();

  const followedTraderData = useMemo(
    () => ALL_TRADERS.filter((t) => followedTraders.includes(t.id)),
    [followedTraders]
  );

  // Simulated copy trading P&L per trader
  const copyPnlData = useMemo(() => {
    const data: Record<string, { pnl: number; trades: number }> = {};
    for (const traderId of followedTraders) {
      const trader = ALL_TRADERS.find((t) => t.id === traderId);
      if (trader && copySettings[traderId]?.enabled) {
        const simPnl = (seededRandom(traderId.length * 7) - 0.3) * 200 * (copySettings[traderId].maxCapitalPercent / 10);
        data[traderId] = {
          pnl: Math.round(simPnl * 100) / 100,
          trades: Math.floor(seededRandom(traderId.length * 13) * 8) + 1,
        };
      }
    }
    return data;
  }, [followedTraders, copySettings]);

  const totalCopiedPnl = Object.values(copyPnlData).reduce((sum, d) => sum + d.pnl, 0);
  const activeCopies = Object.keys(copyPnlData).length;

  return (
    <>
      <AppHeader title="Social Trading" subtitle="Follow & Copy Top Traders" />
      <div className="p-3 sm:p-4 md:p-6 space-y-4 md:space-y-6">
        {/* Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-3 pb-2 px-3">
              <div className="flex items-center gap-2 mb-1">
                <Heart className="h-3.5 w-3.5 text-red-400" />
                <span className="text-[10px] text-muted-foreground">Following</span>
              </div>
              <div className="text-lg font-bold text-white font-mono">
                {followCount}
                {maxFollows !== Infinity && (
                  <span className="text-xs text-muted-foreground font-normal">/{maxFollows}</span>
                )}
              </div>
            </CardContent>
          </Card>
          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-3 pb-2 px-3">
              <div className="flex items-center gap-2 mb-1">
                <Copy className="h-3.5 w-3.5 text-blue-400" />
                <span className="text-[10px] text-muted-foreground">Active Copies</span>
              </div>
              <div className="text-lg font-bold text-white font-mono">{activeCopies}</div>
            </CardContent>
          </Card>
          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-3 pb-2 px-3">
              <div className="flex items-center gap-2 mb-1">
                <DollarSign className="h-3.5 w-3.5 text-green-400" />
                <span className="text-[10px] text-muted-foreground">Copied P&L</span>
              </div>
              <div className={`text-lg font-bold font-mono ${totalCopiedPnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                {totalCopiedPnl >= 0 ? "+" : ""}${totalCopiedPnl.toFixed(2)}
              </div>
            </CardContent>
          </Card>
          <Card className="bg-card/50 border-border/50">
            <CardContent className="pt-3 pb-2 px-3">
              <div className="flex items-center gap-2 mb-1">
                <Activity className="h-3.5 w-3.5 text-purple-400" />
                <span className="text-[10px] text-muted-foreground">Copied Trades</span>
              </div>
              <div className="text-lg font-bold text-white font-mono">
                {Object.values(copyPnlData).reduce((sum, d) => sum + d.trades, 0)}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="following">
          <TabsList>
            <TabsTrigger value="following" className="gap-1">
              <Users className="h-3 w-3" /> Following
            </TabsTrigger>
            <TabsTrigger value="feed" className="gap-1">
              <Activity className="h-3 w-3" /> Activity Feed
            </TabsTrigger>
            <TabsTrigger value="copy" className="gap-1">
              <Copy className="h-3 w-3" /> Copy Trading
            </TabsTrigger>
          </TabsList>

          {/* Following Tab */}
          <TabsContent value="following">
            {followedTraderData.length === 0 ? (
              <Card className="bg-card/50 border-border/50 mt-4">
                <CardContent className="pt-8 pb-8 px-4 text-center">
                  <Users className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
                  <div className="text-sm font-medium text-white mb-1">
                    No traders followed yet
                  </div>
                  <div className="text-xs text-muted-foreground mb-4">
                    Discover top performers on the Leaderboard and follow them to track their trades
                  </div>
                  <Link href="/leaderboard">
                    <Button variant="outline" size="sm" className="text-xs">
                      Browse Leaderboard
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mt-4">
                {followedTraderData.map((trader) => (
                  <TraderProfileCard key={trader.id} trader={trader} />
                ))}
              </div>
            )}
          </TabsContent>

          {/* Activity Feed Tab */}
          <TabsContent value="feed">
            <div className="mt-4">
              <TraderFeed />
            </div>
          </TabsContent>

          {/* Copy Trading Tab */}
          <TabsContent value="copy">
            <div className="mt-4 space-y-3">
              {followedTraderData.length === 0 ? (
                <Card className="bg-card/50 border-border/50">
                  <CardContent className="pt-8 pb-8 px-4 text-center">
                    <Copy className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
                    <div className="text-sm font-medium text-white mb-1">
                      No traders to copy
                    </div>
                    <div className="text-xs text-muted-foreground mb-4">
                      Follow traders first, then configure copy trading settings
                    </div>
                    <Link href="/leaderboard">
                      <Button variant="outline" size="sm" className="text-xs">
                        Browse Leaderboard
                      </Button>
                    </Link>
                  </CardContent>
                </Card>
              ) : (
                followedTraderData.map((trader) => {
                  const settings = copySettings[trader.id] ?? {
                    enabled: false,
                    maxCapitalPercent: 5,
                    autoFollow: false,
                  };
                  const pnlData = copyPnlData[trader.id];

                  return (
                    <Card key={trader.id} className="bg-card/50 border-border/50">
                      <CardContent className="pt-3 pb-3 px-4">
                        <div className="flex items-start gap-3">
                          {/* Trader Info */}
                          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-600/20 text-blue-400 text-xs font-bold">
                            {trader.name.split(/[_\s]+/).slice(0, 2).map((s) => s[0]?.toUpperCase()).join("")}
                          </div>
                          <div className="min-w-0 flex-1 space-y-2">
                            {/* Name row */}
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-medium text-white">{trader.name}</span>
                                <Badge className={`text-[9px] ${trader.tier === "enterprise" ? "bg-purple-500/20 text-purple-400" : trader.tier === "pro" ? "bg-blue-500/20 text-blue-400" : "bg-muted text-muted-foreground"}`}>
                                  {trader.tier}
                                </Badge>
                                <span className={`text-xs font-mono ${trader.totalReturn >= 0 ? "text-green-400" : "text-red-400"}`}>
                                  {trader.totalReturn >= 0 ? "+" : ""}{trader.totalReturn.toFixed(1)}%
                                </span>
                              </div>
                            </div>

                            {/* Settings */}
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                              {/* Enable/Disable */}
                              <div className="flex items-center justify-between sm:flex-col sm:items-start gap-1">
                                <span className="text-[10px] text-muted-foreground">Copy Trades</span>
                                <Switch
                                  checked={settings.enabled}
                                  onCheckedChange={(checked) => setCopySettings(trader.id, { enabled: checked })}
                                />
                              </div>

                              {/* Capital Allocation */}
                              <div className="space-y-1">
                                <div className="flex items-center justify-between">
                                  <span className="text-[10px] text-muted-foreground">Max Capital</span>
                                  <span className="text-[10px] font-mono text-white">{settings.maxCapitalPercent}%</span>
                                </div>
                                <input
                                  type="range"
                                  min={1}
                                  max={50}
                                  value={settings.maxCapitalPercent}
                                  onChange={(e) => setCopySettings(trader.id, { maxCapitalPercent: Number(e.target.value) })}
                                  className="w-full h-1 bg-muted rounded-full appearance-none cursor-pointer accent-blue-600"
                                  disabled={!settings.enabled}
                                />
                              </div>

                              {/* Auto-Follow */}
                              <div className="flex items-center justify-between sm:flex-col sm:items-start gap-1">
                                <span className="text-[10px] text-muted-foreground">Auto-Follow</span>
                                <Switch
                                  checked={settings.autoFollow}
                                  onCheckedChange={(checked) => setCopySettings(trader.id, { autoFollow: checked })}
                                  disabled={!settings.enabled}
                                />
                              </div>
                            </div>

                            {/* Performance Attribution */}
                            {pnlData && (
                              <div className="border-t border-border/30 pt-2 flex items-center gap-4">
                                <div className="flex items-center gap-1">
                                  {pnlData.pnl >= 0 ? (
                                    <TrendingUp className="h-3 w-3 text-green-400" />
                                  ) : (
                                    <TrendingDown className="h-3 w-3 text-red-400" />
                                  )}
                                  <span className={`text-xs font-mono font-medium ${pnlData.pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                                    {pnlData.pnl >= 0 ? "+" : ""}${pnlData.pnl.toFixed(2)}
                                  </span>
                                  <span className="text-[9px] text-muted-foreground">copied P&L</span>
                                </div>
                                <div className="text-[10px] text-muted-foreground">
                                  {pnlData.trades} trades copied
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </>
  );
}
