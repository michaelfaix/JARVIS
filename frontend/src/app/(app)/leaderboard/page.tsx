// =============================================================================
// src/app/(app)/leaderboard/page.tsx — Community Leaderboard
// =============================================================================

"use client";

import { useMemo } from "react";
import { HudPanel } from "@/components/ui/hud-panel";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { usePortfolio } from "@/hooks/use-portfolio";
import { useProfile } from "@/hooks/use-profile";
import { Button } from "@/components/ui/button";
import { useSocialTrading } from "@/hooks/use-social-trading";
import {
  Trophy,
  Medal,
  TrendingUp,
  Target,
  BarChart3,
  Crown,
  User,
  Heart,
  Copy,
} from "lucide-react";

// Simulated leaderboard data (in production, this comes from Supabase)
interface LeaderboardEntry {
  rank: number;
  name: string;
  tier: "free" | "pro" | "enterprise";
  totalReturn: number;
  winRate: number;
  trades: number;
  drawdown: number;
  isCurrentUser?: boolean;
}

function generateLeaderboard(
  currentUser: {
    name: string;
    tier: string;
    totalReturn: number;
    winRate: number;
    trades: number;
    drawdown: number;
  } | null
): LeaderboardEntry[] {
  // Simulated top traders
  const simulated: Omit<LeaderboardEntry, "rank">[] = [
    { name: "CryptoWhale_99", tier: "enterprise", totalReturn: 34.2, winRate: 72, trades: 156, drawdown: 4.1 },
    { name: "AlgoTrader_Pro", tier: "pro", totalReturn: 28.7, winRate: 68, trades: 243, drawdown: 5.3 },
    { name: "JarvisBot_1", tier: "enterprise", totalReturn: 24.1, winRate: 65, trades: 412, drawdown: 3.8 },
    { name: "MomentumKing", tier: "pro", totalReturn: 19.5, winRate: 61, trades: 89, drawdown: 7.2 },
    { name: "Sven_Berlin", tier: "pro", totalReturn: 16.8, winRate: 59, trades: 67, drawdown: 6.1 },
    { name: "TrendFollower", tier: "free", totalReturn: 14.3, winRate: 57, trades: 45, drawdown: 8.4 },
    { name: "SmartMoneyFx", tier: "pro", totalReturn: 12.1, winRate: 55, trades: 112, drawdown: 5.9 },
    { name: "DayTraderMax", tier: "free", totalReturn: 9.8, winRate: 53, trades: 198, drawdown: 9.1 },
    { name: "SwingSetup_AI", tier: "pro", totalReturn: 7.4, winRate: 51, trades: 34, drawdown: 4.5 },
    { name: "HODLer2024", tier: "free", totalReturn: 5.2, winRate: 50, trades: 12, drawdown: 11.2 },
    { name: "ScalpMaster", tier: "free", totalReturn: 3.1, winRate: 48, trades: 301, drawdown: 6.8 },
    { name: "NoviceTrader", tier: "free", totalReturn: -2.4, winRate: 42, trades: 28, drawdown: 14.5 },
  ];

  // Insert current user if they have trades
  const all = [...simulated];
  if (currentUser && currentUser.trades > 0) {
    all.push({
      name: currentUser.name,
      tier: currentUser.tier as "free" | "pro" | "enterprise",
      totalReturn: currentUser.totalReturn,
      winRate: currentUser.winRate,
      trades: currentUser.trades,
      drawdown: currentUser.drawdown,
      isCurrentUser: true,
    });
  }

  // Sort by total return
  all.sort((a, b) => b.totalReturn - a.totalReturn);

  return all.map((entry, i) => ({ ...entry, rank: i + 1 }));
}

const RANK_ICONS = [
  <Trophy key="1" className="h-4 w-4 text-hud-amber" />,
  <Medal key="2" className="h-4 w-4 text-gray-300" />,
  <Medal key="3" className="h-4 w-4 text-amber-600" />,
];

const TIER_BADGE: Record<string, string> = {
  enterprise: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  pro: "bg-hud-cyan/20 text-hud-cyan border-hud-cyan/30",
  free: "bg-hud-bg/60 text-muted-foreground border-hud-border/30",
};

export default function LeaderboardPage() {
  const { state: portfolio, winRate, drawdown, totalValue } = usePortfolio();
  const { profile, tier } = useProfile();
  const { isFollowing, followTrader, unfollowTrader, canFollow } = useSocialTrading();

  const totalReturn =
    portfolio.totalCapital > 0
      ? ((totalValue - portfolio.totalCapital) / portfolio.totalCapital) * 100
      : 0;

  const leaderboard = useMemo(
    () =>
      generateLeaderboard(
        profile
          ? {
              name: profile.displayName,
              tier,
              totalReturn,
              winRate,
              trades: portfolio.closedTrades.length,
              drawdown,
            }
          : null
      ),
    [profile, tier, totalReturn, winRate, portfolio.closedTrades.length, drawdown]
  );

  const currentUserEntry = leaderboard.find((e) => e.isCurrentUser);

  return (
    <div className="p-2 sm:p-3 md:p-4 space-y-3">
      {/* Top 3 Podium */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {leaderboard.slice(0, 3).map((entry, i) => (
          <HudPanel
            key={entry.name}
            className={`${
              i === 0 ? "md:order-2 ring-1 ring-hud-amber/30" : i === 1 ? "md:order-1" : "md:order-3"
            } ${entry.isCurrentUser ? "ring-1 ring-hud-cyan/50" : ""}`}
          >
            <div className="pt-4 pb-3 px-3 text-center">
              <div className="mb-2">{RANK_ICONS[i]}</div>
              <div className="text-[10px] text-muted-foreground font-mono mb-1">
                #{entry.rank}
              </div>
              <div className="font-bold text-white text-sm flex items-center justify-center gap-1.5 font-mono">
                {entry.isCurrentUser && <User className="h-3 w-3 text-hud-cyan" />}
                {entry.name}
              </div>
              <Badge className={`mt-1 text-[9px] ${TIER_BADGE[entry.tier]}`}>
                {entry.tier}
              </Badge>
              <div
                className={`text-2xl font-bold font-mono mt-2 ${
                  entry.totalReturn >= 0 ? "text-hud-green" : "text-hud-red"
                }`}
              >
                {entry.totalReturn >= 0 ? "+" : ""}
                {entry.totalReturn.toFixed(1)}%
              </div>
              <div className="text-[10px] text-muted-foreground mt-1 font-mono">
                {entry.trades} trades · {entry.winRate}% win
              </div>
            </div>
          </HudPanel>
        ))}
      </div>

      {/* Your Position */}
      {currentUserEntry && (
        <HudPanel title="YOUR POSITION" className="bg-hud-cyan/5 border-hud-cyan/20">
          <div className="p-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-hud-cyan/20">
                  <Crown className="h-5 w-5 text-hud-cyan" />
                </div>
                <div>
                  <div className="text-sm font-bold text-white font-mono">
                    Rank #{currentUserEntry.rank}
                  </div>
                  <div className="text-[10px] text-muted-foreground font-mono">
                    of {leaderboard.length} traders
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div
                  className={`text-xl font-bold font-mono ${
                    currentUserEntry.totalReturn >= 0
                      ? "text-hud-green"
                      : "text-hud-red"
                  }`}
                >
                  {currentUserEntry.totalReturn >= 0 ? "+" : ""}
                  {currentUserEntry.totalReturn.toFixed(1)}%
                </div>
                <div className="text-[10px] text-muted-foreground font-mono">
                  Total Return
                </div>
              </div>
            </div>
          </div>
        </HudPanel>
      )}

      {/* Full Ranking Table */}
      <Tabs defaultValue="return">
        <TabsList className="bg-hud-bg/60 border border-hud-border/30">
          <TabsTrigger value="return" className="gap-1 data-[state=active]:text-hud-cyan">
            <TrendingUp className="h-3 w-3" /> Return
          </TabsTrigger>
          <TabsTrigger value="winrate" className="gap-1 data-[state=active]:text-hud-cyan">
            <Target className="h-3 w-3" /> Win Rate
          </TabsTrigger>
          <TabsTrigger value="risk" className="gap-1 data-[state=active]:text-hud-cyan">
            <BarChart3 className="h-3 w-3" /> Risk-Adjusted
          </TabsTrigger>
        </TabsList>

        <TabsContent value="return">
          <RankingTable
            entries={[...leaderboard].sort(
              (a, b) => b.totalReturn - a.totalReturn
            )}
            sortKey="totalReturn"
            isFollowing={isFollowing}
            followTrader={followTrader}
            unfollowTrader={unfollowTrader}
            canFollow={canFollow}
          />
        </TabsContent>
        <TabsContent value="winrate">
          <RankingTable
            entries={[...leaderboard].sort((a, b) => b.winRate - a.winRate)}
            sortKey="winRate"
            isFollowing={isFollowing}
            followTrader={followTrader}
            unfollowTrader={unfollowTrader}
            canFollow={canFollow}
          />
        </TabsContent>
        <TabsContent value="risk">
          <RankingTable
            entries={[...leaderboard].sort((a, b) => {
              const aScore =
                a.drawdown > 0 ? a.totalReturn / a.drawdown : a.totalReturn;
              const bScore =
                b.drawdown > 0 ? b.totalReturn / b.drawdown : b.totalReturn;
              return bScore - aScore;
            })}
            sortKey="riskAdjusted"
            isFollowing={isFollowing}
            followTrader={followTrader}
            unfollowTrader={unfollowTrader}
            canFollow={canFollow}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function RankingTable({
  entries,
  sortKey,
  isFollowing,
  followTrader,
  unfollowTrader,
  canFollow,
}: {
  entries: LeaderboardEntry[];
  sortKey: string;
  isFollowing: (id: string) => boolean;
  followTrader: (id: string) => void;
  unfollowTrader: (id: string) => void;
  canFollow: boolean;
}) {
  return (
    <HudPanel title="RANKINGS" className="mt-4">
      <div className="p-2.5">
        <div className="overflow-x-auto">
          <Table className="border-hud-border/30">
            <TableHeader>
              <TableRow className="border-hud-border/30">
                <TableHead className="w-12 font-mono text-[10px]">#</TableHead>
                <TableHead className="font-mono text-[10px]">Trader</TableHead>
                <TableHead className="font-mono text-[10px]">Tier</TableHead>
                <TableHead className="text-right font-mono text-[10px]">Return</TableHead>
                <TableHead className="text-right font-mono text-[10px]">Win Rate</TableHead>
                <TableHead className="text-right font-mono text-[10px]">Trades</TableHead>
                <TableHead className="text-right font-mono text-[10px]">Max DD</TableHead>
                {sortKey === "riskAdjusted" && (
                  <TableHead className="text-right font-mono text-[10px]">Score</TableHead>
                )}
                <TableHead className="text-center w-20 font-mono text-[10px]">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {entries.map((entry, i) => {
                const following = !entry.isCurrentUser && isFollowing(entry.name);
                return (
                <TableRow
                  key={entry.name}
                  className={`border-hud-border/30 ${
                    entry.isCurrentUser
                      ? "bg-hud-cyan/5 border-hud-cyan/20"
                      : ""
                  }`}
                >
                  <TableCell className="font-mono text-muted-foreground">
                    {i < 3 ? RANK_ICONS[i] : i + 1}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1.5">
                      {entry.isCurrentUser && (
                        <User className="h-3 w-3 text-hud-cyan" />
                      )}
                      <span
                        className={`font-medium font-mono ${
                          entry.isCurrentUser ? "text-hud-cyan" : "text-white"
                        }`}
                      >
                        {entry.name}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={`text-[9px] ${TIER_BADGE[entry.tier]}`}
                    >
                      {entry.tier}
                    </Badge>
                  </TableCell>
                  <TableCell
                    className={`text-right font-mono ${
                      entry.totalReturn >= 0 ? "text-hud-green" : "text-hud-red"
                    }`}
                  >
                    {entry.totalReturn >= 0 ? "+" : ""}
                    {entry.totalReturn.toFixed(1)}%
                  </TableCell>
                  <TableCell className="text-right font-mono text-white">
                    {entry.winRate}%
                  </TableCell>
                  <TableCell className="text-right font-mono text-muted-foreground">
                    {entry.trades}
                  </TableCell>
                  <TableCell
                    className={`text-right font-mono ${
                      entry.drawdown > 10
                        ? "text-hud-red"
                        : entry.drawdown > 5
                        ? "text-hud-amber"
                        : "text-hud-green"
                    }`}
                  >
                    {entry.drawdown.toFixed(1)}%
                  </TableCell>
                  {sortKey === "riskAdjusted" && (
                    <TableCell className="text-right font-mono text-white">
                      {entry.drawdown > 0
                        ? (entry.totalReturn / entry.drawdown).toFixed(2)
                        : "—"}
                    </TableCell>
                  )}
                  <TableCell className="text-center">
                    {!entry.isCurrentUser && (
                      <div className="flex items-center justify-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0"
                          onClick={() => following ? unfollowTrader(entry.name) : followTrader(entry.name)}
                          disabled={!following && !canFollow}
                          title={following ? "Unfollow" : canFollow ? "Follow" : "Max follows reached"}
                        >
                          <Heart
                            className={`h-3.5 w-3.5 ${
                              following
                                ? "fill-hud-red text-hud-red"
                                : "text-muted-foreground hover:text-hud-red"
                            }`}
                          />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0"
                          title="Copy trades"
                          onClick={() => {
                            if (!following) followTrader(entry.name);
                          }}
                        >
                          <Copy className="h-3.5 w-3.5 text-muted-foreground hover:text-hud-cyan" />
                        </Button>
                      </div>
                    )}
                  </TableCell>
                </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </div>
    </HudPanel>
  );
}
