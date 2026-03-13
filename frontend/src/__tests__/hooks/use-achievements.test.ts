// =============================================================================
// Tests: use-achievements.ts — Trading achievements / gamification
// =============================================================================

import { renderHook } from "@testing-library/react";
import { useAchievements } from "@/hooks/use-achievements";
import type { ClosedTrade } from "@/lib/types";

function makeTrade(overrides?: Partial<ClosedTrade>): ClosedTrade {
  return {
    id: `trade-${Date.now()}-${Math.random()}`,
    asset: "BTC",
    direction: "LONG",
    entryPrice: 60000,
    exitPrice: 61000,
    size: 1,
    capitalAllocated: 60000,
    openedAt: "2024-01-01T00:00:00Z",
    closedAt: "2024-01-02T00:00:00Z",
    pnl: 1000,
    pnlPercent: 1.67,
    ...overrides,
  };
}

describe("useAchievements", () => {
  it("returns a list of achievement objects", () => {
    const { result } = renderHook(() =>
      useAchievements([], 100000, 100000, 0, 0)
    );

    expect(result.current).toBeInstanceOf(Array);
    expect(result.current.length).toBeGreaterThan(0);

    for (const a of result.current) {
      expect(a).toHaveProperty("id");
      expect(a).toHaveProperty("title");
      expect(a).toHaveProperty("description");
      expect(a).toHaveProperty("unlocked");
      expect(a).toHaveProperty("progress");
      expect(a).toHaveProperty("tier");
    }
  });

  it("all achievements are locked with no trades", () => {
    const { result } = renderHook(() =>
      useAchievements([], 100000, 100000, 0, 0)
    );

    for (const a of result.current) {
      expect(a.unlocked).toBe(false);
    }
  });

  it("unlocks 'first-trade' after 1 closed trade", () => {
    const trades = [makeTrade()];
    const { result } = renderHook(() =>
      useAchievements(trades, 101000, 100000, 100, 0)
    );

    const firstTrade = result.current.find((a) => a.id === "first-trade");
    expect(firstTrade?.unlocked).toBe(true);
    expect(firstTrade?.progress).toBe(100);
  });

  it("unlocks 'first-win' when a profitable trade exists", () => {
    const trades = [makeTrade({ pnl: 500 })];
    const { result } = renderHook(() =>
      useAchievements(trades, 100500, 100000, 100, 0)
    );

    const firstWin = result.current.find((a) => a.id === "first-win");
    expect(firstWin?.unlocked).toBe(true);
  });

  it("does not unlock 'first-win' when only losing trades exist", () => {
    const trades = [makeTrade({ pnl: -500 })];
    const { result } = renderHook(() =>
      useAchievements(trades, 99500, 100000, 0, 0.5)
    );

    const firstWin = result.current.find((a) => a.id === "first-win");
    expect(firstWin?.unlocked).toBe(false);
  });

  it("unlocks 'ten-trades' after 10 trades", () => {
    const trades = Array.from({ length: 10 }, () => makeTrade());
    const { result } = renderHook(() =>
      useAchievements(trades, 110000, 100000, 100, 0)
    );

    const tenTrades = result.current.find((a) => a.id === "ten-trades");
    expect(tenTrades?.unlocked).toBe(true);
  });

  it("tracks progress for partial completion", () => {
    const trades = Array.from({ length: 5 }, () => makeTrade());
    const { result } = renderHook(() =>
      useAchievements(trades, 105000, 100000, 60, 2)
    );

    const tenTrades = result.current.find((a) => a.id === "ten-trades");
    expect(tenTrades?.unlocked).toBe(false);
    expect(tenTrades?.progress).toBe(50); // 5/10 * 100
  });

  it("unlocks 'return-5' when total return >= 5%", () => {
    const trades = [makeTrade({ pnl: 5000 })];
    // totalValue = 105000, initialCapital = 100000 → 5% return
    const { result } = renderHook(() =>
      useAchievements(trades, 105000, 100000, 100, 0)
    );

    const return5 = result.current.find((a) => a.id === "return-5");
    expect(return5?.unlocked).toBe(true);
  });

  it("unlocks 'winrate-50' with 50%+ win rate and 10+ trades", () => {
    const wins = Array.from({ length: 6 }, (_, i) =>
      makeTrade({ id: `w${i}`, pnl: 100 })
    );
    const losses = Array.from({ length: 4 }, (_, i) =>
      makeTrade({ id: `l${i}`, pnl: -50 })
    );
    const trades = [...wins, ...losses];
    // 60% win rate, 10 trades
    const { result } = renderHook(() =>
      useAchievements(trades, 100400, 100000, 60, 1)
    );

    const wr50 = result.current.find((a) => a.id === "winrate-50");
    expect(wr50?.unlocked).toBe(true);
  });

  it("does not unlock 'winrate-50' with < 10 trades", () => {
    const trades = Array.from({ length: 5 }, () =>
      makeTrade({ pnl: 100 })
    );
    const { result } = renderHook(() =>
      useAchievements(trades, 100500, 100000, 100, 0)
    );

    const wr50 = result.current.find((a) => a.id === "winrate-50");
    expect(wr50?.unlocked).toBe(false);
  });

  it("unlocks 'streak-3' with 3 consecutive wins", () => {
    const trades = [
      makeTrade({ pnl: 100, closedAt: "2024-01-03T00:00:00Z" }),
      makeTrade({ pnl: 200, closedAt: "2024-01-02T00:00:00Z" }),
      makeTrade({ pnl: 150, closedAt: "2024-01-01T00:00:00Z" }),
    ];
    const { result } = renderHook(() =>
      useAchievements(trades, 100450, 100000, 100, 0)
    );

    const streak3 = result.current.find((a) => a.id === "streak-3");
    expect(streak3?.unlocked).toBe(true);
  });

  it("unlocks 'low-dd' when drawdown < 5% with 10+ trades", () => {
    const trades = Array.from({ length: 12 }, () => makeTrade());
    const { result } = renderHook(() =>
      useAchievements(trades, 112000, 100000, 100, 3)
    );

    const lowDD = result.current.find((a) => a.id === "low-dd");
    expect(lowDD?.unlocked).toBe(true);
  });

  it("does not unlock 'low-dd' when drawdown >= 5%", () => {
    const trades = Array.from({ length: 12 }, () => makeTrade());
    const { result } = renderHook(() =>
      useAchievements(trades, 95000, 100000, 50, 6)
    );

    const lowDD = result.current.find((a) => a.id === "low-dd");
    expect(lowDD?.unlocked).toBe(false);
  });

  it("unlocks 'big-win' when a single trade has 10%+ return", () => {
    const trades = [makeTrade({ pnlPercent: 12 })];
    const { result } = renderHook(() =>
      useAchievements(trades, 107200, 100000, 100, 0)
    );

    const bigWin = result.current.find((a) => a.id === "big-win");
    expect(bigWin?.unlocked).toBe(true);
  });

  it("each achievement has a valid tier", () => {
    const { result } = renderHook(() =>
      useAchievements([], 100000, 100000, 0, 0)
    );

    for (const a of result.current) {
      expect(["bronze", "silver", "gold"]).toContain(a.tier);
    }
  });
});
