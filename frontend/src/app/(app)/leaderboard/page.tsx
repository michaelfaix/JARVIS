// =============================================================================
// src/app/(app)/leaderboard/page.tsx — Community Leaderboard
// =============================================================================

"use client";

import { useMemo } from "react";
import { AppHeader } from "@/components/layout/app-header";
import { Card, CardContent } from "@/components/ui/card";
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
import {
  Trophy,
  Medal,
  TrendingUp,
  Target,
  BarChart3,
  Crown,
  User,
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
  <Trophy key="1" className="h-4 w-4 text-yellow-400" />,
  <Medal key="2" className="h-4 w-4 text-gray-300" />,
  <Medal key="3" className="h-4 w-4 text-amber-600" />,
];

const TIER_BADGE: Record<string, string> = {
  enterprise: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  pro: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  free: "bg-muted text-muted-foreground border-border/50",
};

export default function LeaderboardPage() {
  const { state: portfolio, winRate, drawdown, totalValue } = usePortfolio();
  const { profile, tier } = useProfile();

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
    <>
      <AppHeader title="Leaderboard" subtitle="Community Rankings" />
      <div className="p-6 space-y-6">
        {/* Top 3 Podium */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {leaderboard.slice(0, 3).map((entry, i) => (
            <Card
              key={entry.name}
              className={`bg-card/50 border-border/50 ${
                i === 0 ? "md:order-2 ring-1 ring-yellow-500/30" : i === 1 ? "md:order-1" : "md:order-3"
              } ${entry.isCurrentUser ? "ring-1 ring-blue-500/50" : ""}`}
            >
              <CardContent className="pt-5 pb-4 px-4 text-center">
                <div className="mb-2">{RANK_ICONS[i]}</div>
                <div className="text-xs text-muted-foreground mb-1">
                  #{entry.rank}
                </div>
                <div className="font-bold text-white text-sm flex items-center justify-center gap-1.5">
                  {entry.isCurrentUser && <User className="h-3 w-3 text-blue-400" />}
                  {entry.name}
                </div>
                <Badge className={`mt-1 text-[9px] ${TIER_BADGE[entry.tier]}`}>
                  {entry.tier}
                </Badge>
                <div
                  className={`text-2xl font-bold font-mono mt-2 ${
                    entry.totalReturn >= 0 ? "text-green-400" : "text-red-400"
                  }`}
                >
                  {entry.totalReturn >= 0 ? "+" : ""}
                  {entry.totalReturn.toFixed(1)}%
                </div>
                <div className="text-[10px] text-muted-foreground mt-1">
                  {entry.trades} trades · {entry.winRate}% win
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Your Position */}
        {currentUserEntry && (
          <Card className="bg-blue-600/5 border-blue-500/20">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600/20">
                    <Crown className="h-5 w-5 text-blue-400" />
                  </div>
                  <div>
                    <div className="text-sm font-bold text-white">
                      Your Position: #{currentUserEntry.rank}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      of {leaderboard.length} traders
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div
                    className={`text-xl font-bold font-mono ${
                      currentUserEntry.totalReturn >= 0
                        ? "text-green-400"
                        : "text-red-400"
                    }`}
                  >
                    {currentUserEntry.totalReturn >= 0 ? "+" : ""}
                    {currentUserEntry.totalReturn.toFixed(1)}%
                  </div>
                  <div className="text-[10px] text-muted-foreground">
                    Total Return
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Full Ranking Table */}
        <Tabs defaultValue="return">
          <TabsList>
            <TabsTrigger value="return" className="gap-1">
              <TrendingUp className="h-3 w-3" /> Return
            </TabsTrigger>
            <TabsTrigger value="winrate" className="gap-1">
              <Target className="h-3 w-3" /> Win Rate
            </TabsTrigger>
            <TabsTrigger value="risk" className="gap-1">
              <BarChart3 className="h-3 w-3" /> Risk-Adjusted
            </TabsTrigger>
          </TabsList>

          <TabsContent value="return">
            <RankingTable
              entries={[...leaderboard].sort(
                (a, b) => b.totalReturn - a.totalReturn
              )}
              sortKey="totalReturn"
            />
          </TabsContent>
          <TabsContent value="winrate">
            <RankingTable
              entries={[...leaderboard].sort((a, b) => b.winRate - a.winRate)}
              sortKey="winRate"
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
            />
          </TabsContent>
        </Tabs>
      </div>
    </>
  );
}

function RankingTable({
  entries,
  sortKey,
}: {
  entries: LeaderboardEntry[];
  sortKey: string;
}) {
  return (
    <Card className="bg-card/50 border-border/50 mt-4">
      <CardContent className="pt-0 px-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-12">#</TableHead>
              <TableHead>Trader</TableHead>
              <TableHead>Tier</TableHead>
              <TableHead className="text-right">Return</TableHead>
              <TableHead className="text-right">Win Rate</TableHead>
              <TableHead className="text-right">Trades</TableHead>
              <TableHead className="text-right">Max DD</TableHead>
              {sortKey === "riskAdjusted" && (
                <TableHead className="text-right">Score</TableHead>
              )}
            </TableRow>
          </TableHeader>
          <TableBody>
            {entries.map((entry, i) => (
              <TableRow
                key={entry.name}
                className={
                  entry.isCurrentUser
                    ? "bg-blue-500/5 border-blue-500/20"
                    : ""
                }
              >
                <TableCell className="font-mono text-muted-foreground">
                  {i < 3 ? RANK_ICONS[i] : i + 1}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1.5">
                    {entry.isCurrentUser && (
                      <User className="h-3 w-3 text-blue-400" />
                    )}
                    <span
                      className={`font-medium ${
                        entry.isCurrentUser ? "text-blue-400" : "text-white"
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
                    entry.totalReturn >= 0 ? "text-green-400" : "text-red-400"
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
                      ? "text-red-400"
                      : entry.drawdown > 5
                      ? "text-yellow-400"
                      : "text-green-400"
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
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
