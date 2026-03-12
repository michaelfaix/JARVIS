// =============================================================================
// src/hooks/use-achievements.ts — Trading achievements / gamification
// =============================================================================

"use client";

import { useMemo } from "react";
import type { ClosedTrade } from "@/lib/types";

export interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: string; // emoji
  unlocked: boolean;
  progress: number; // 0-100
  tier: "bronze" | "silver" | "gold";
}

export function useAchievements(
  closedTrades: ClosedTrade[],
  totalValue: number,
  initialCapital: number,
  winRate: number,
  drawdown: number
): Achievement[] {
  return useMemo(() => {
    const wins = closedTrades.filter((t) => t.pnl > 0).length;
    const totalReturn =
      initialCapital > 0
        ? ((totalValue - initialCapital) / initialCapital) * 100
        : 0;

    const bestTrade = closedTrades.length > 0
      ? Math.max(...closedTrades.map((t) => t.pnlPercent))
      : 0;

    const streak = getWinStreak(closedTrades);

    return [
      // Trading volume
      {
        id: "first-trade",
        title: "First Blood",
        description: "Close your first trade",
        icon: "⚔️",
        unlocked: closedTrades.length >= 1,
        progress: Math.min(100, (closedTrades.length / 1) * 100),
        tier: "bronze" as const,
      },
      {
        id: "ten-trades",
        title: "Getting Started",
        description: "Complete 10 trades",
        icon: "📊",
        unlocked: closedTrades.length >= 10,
        progress: Math.min(100, (closedTrades.length / 10) * 100),
        tier: "bronze" as const,
      },
      {
        id: "fifty-trades",
        title: "Seasoned Trader",
        description: "Complete 50 trades",
        icon: "🎯",
        unlocked: closedTrades.length >= 50,
        progress: Math.min(100, (closedTrades.length / 50) * 100),
        tier: "silver" as const,
      },
      {
        id: "hundred-trades",
        title: "Market Veteran",
        description: "Complete 100 trades",
        icon: "🏆",
        unlocked: closedTrades.length >= 100,
        progress: Math.min(100, (closedTrades.length / 100) * 100),
        tier: "gold" as const,
      },

      // Profitability
      {
        id: "first-win",
        title: "Winner",
        description: "Close a profitable trade",
        icon: "💰",
        unlocked: wins >= 1,
        progress: Math.min(100, (wins / 1) * 100),
        tier: "bronze" as const,
      },
      {
        id: "return-5",
        title: "Profit Machine",
        description: "Achieve +5% total return",
        icon: "📈",
        unlocked: totalReturn >= 5,
        progress: Math.min(100, (totalReturn / 5) * 100),
        tier: "silver" as const,
      },
      {
        id: "return-20",
        title: "Master Trader",
        description: "Achieve +20% total return",
        icon: "🚀",
        unlocked: totalReturn >= 20,
        progress: Math.min(100, (totalReturn / 20) * 100),
        tier: "gold" as const,
      },

      // Win rate
      {
        id: "winrate-50",
        title: "Coin Flipper",
        description: "Maintain 50%+ win rate (10+ trades)",
        icon: "🎲",
        unlocked: winRate >= 50 && closedTrades.length >= 10,
        progress: closedTrades.length >= 10 ? Math.min(100, (winRate / 50) * 100) : (closedTrades.length / 10) * 100,
        tier: "bronze" as const,
      },
      {
        id: "winrate-65",
        title: "Sharp Shooter",
        description: "Maintain 65%+ win rate (20+ trades)",
        icon: "🎯",
        unlocked: winRate >= 65 && closedTrades.length >= 20,
        progress: closedTrades.length >= 20 ? Math.min(100, (winRate / 65) * 100) : (closedTrades.length / 20) * 100,
        tier: "gold" as const,
      },

      // Streaks
      {
        id: "streak-3",
        title: "Hot Streak",
        description: "Win 3 trades in a row",
        icon: "🔥",
        unlocked: streak >= 3,
        progress: Math.min(100, (streak / 3) * 100),
        tier: "bronze" as const,
      },
      {
        id: "streak-5",
        title: "On Fire",
        description: "Win 5 trades in a row",
        icon: "💎",
        unlocked: streak >= 5,
        progress: Math.min(100, (streak / 5) * 100),
        tier: "silver" as const,
      },

      // Risk management
      {
        id: "low-dd",
        title: "Risk Manager",
        description: "Keep max drawdown under 5% (10+ trades)",
        icon: "🛡️",
        unlocked: drawdown < 5 && closedTrades.length >= 10,
        progress: closedTrades.length >= 10 ? (drawdown < 5 ? 100 : Math.max(0, (1 - drawdown / 10) * 100)) : (closedTrades.length / 10) * 100,
        tier: "silver" as const,
      },

      // Best trade
      {
        id: "big-win",
        title: "Jackpot",
        description: "Close a single trade with 10%+ return",
        icon: "🎰",
        unlocked: bestTrade >= 10,
        progress: Math.min(100, (bestTrade / 10) * 100),
        tier: "gold" as const,
      },
    ];
  }, [closedTrades, totalValue, initialCapital, winRate, drawdown]);
}

function getWinStreak(trades: ClosedTrade[]): number {
  // Sort by closed date, most recent first
  const sorted = [...trades].sort(
    (a, b) => new Date(b.closedAt).getTime() - new Date(a.closedAt).getTime()
  );

  let maxStreak = 0;
  let currentStreak = 0;

  for (const trade of sorted) {
    if (trade.pnl > 0) {
      currentStreak++;
      maxStreak = Math.max(maxStreak, currentStreak);
    } else {
      currentStreak = 0;
    }
  }

  return maxStreak;
}
