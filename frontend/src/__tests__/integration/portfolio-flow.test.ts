// =============================================================================
// Integration: portfolio-flow — Open, update, close positions with P&L checks
// =============================================================================

import { renderHook, act } from "@testing-library/react";
import { usePortfolio } from "@/hooks/use-portfolio";

// Mock Supabase
jest.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    from: () => ({
      upsert: jest.fn().mockReturnValue({ then: (cb: () => void) => cb() }),
      insert: jest.fn().mockReturnValue({ then: (cb: () => void) => cb() }),
      select: () => ({
        eq: () => ({
          single: () => Promise.resolve({ data: null }),
          order: () => ({
            limit: () => Promise.resolve({ data: [] }),
          }),
        }),
      }),
    }),
  }),
}));

// Mock useAuth
jest.mock("@/hooks/use-auth", () => ({
  useAuth: () => ({ user: null, loading: false, signOut: jest.fn() }),
}));

describe("Portfolio Integration Flow", () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  it("open LONG → update price up → close → verify profit P&L", () => {
    const { result } = renderHook(() => usePortfolio());

    // 1. Open LONG position on BTC at $65,000
    act(() => {
      result.current.openPosition({
        asset: "BTC",
        direction: "LONG",
        entryPrice: 65000,
        size: 0.5,
        capitalAllocated: 32500,
        openedAt: "2024-01-01T00:00:00Z",
      });
    });

    expect(result.current.state.positions).toHaveLength(1);
    expect(result.current.state.availableCapital).toBe(100_000 - 32500);
    const posId = result.current.state.positions[0].id;

    // 2. Price increases to $67,000 → unrealized profit
    act(() => {
      result.current.updatePrices({ BTC: 67000 });
    });

    const pos = result.current.state.positions[0];
    const expectedPnl = (67000 - 65000) * 0.5; // $1,000
    expect(pos.pnl).toBe(expectedPnl);
    expect(pos.pnlPercent).toBeCloseTo((expectedPnl / 32500) * 100, 2);
    expect(result.current.unrealizedPnl).toBe(expectedPnl);

    // 3. Close position
    act(() => {
      result.current.closePosition(posId);
    });

    expect(result.current.state.positions).toHaveLength(0);
    expect(result.current.state.closedTrades).toHaveLength(1);
    expect(result.current.state.closedTrades[0].pnl).toBe(expectedPnl);
    expect(result.current.state.realizedPnl).toBe(expectedPnl);
    // Available capital returned = 32500 (allocated) + 1000 (profit) = 33500
    expect(result.current.state.availableCapital).toBe(100_000 + expectedPnl);
  });

  it("open LONG → update price down → close → verify loss P&L", () => {
    const { result } = renderHook(() => usePortfolio());

    act(() => {
      result.current.openPosition({
        asset: "ETH",
        direction: "LONG",
        entryPrice: 3200,
        size: 5,
        capitalAllocated: 16000,
        openedAt: "2024-01-01T00:00:00Z",
      });
    });

    const posId = result.current.state.positions[0].id;

    // Price drops to $3000 → loss
    act(() => {
      result.current.updatePrices({ ETH: 3000 });
    });

    const loss = (3000 - 3200) * 5; // -$1,000
    expect(result.current.state.positions[0].pnl).toBe(loss);

    act(() => {
      result.current.closePosition(posId);
    });

    expect(result.current.state.closedTrades[0].pnl).toBe(loss);
    expect(result.current.state.realizedPnl).toBe(loss);
    expect(result.current.state.availableCapital).toBe(100_000 + loss);
    expect(result.current.winRate).toBe(0); // 0 wins, 1 loss
  });

  it("open SHORT → price drops → close → verify profit", () => {
    const { result } = renderHook(() => usePortfolio());

    act(() => {
      result.current.openPosition({
        asset: "SOL",
        direction: "SHORT",
        entryPrice: 150,
        size: 100,
        capitalAllocated: 15000,
        openedAt: "2024-01-01T00:00:00Z",
      });
    });

    const posId = result.current.state.positions[0].id;

    // Price drops to $140 → profit for SHORT
    act(() => {
      result.current.updatePrices({ SOL: 140 });
    });

    const pnl = (150 - 140) * 100; // $1,000
    expect(result.current.state.positions[0].pnl).toBe(pnl);

    act(() => {
      result.current.closePosition(posId);
    });

    expect(result.current.state.closedTrades[0].pnl).toBe(pnl);
    expect(result.current.winRate).toBe(100);
  });

  it("multiple positions → partial close → check stats", () => {
    const { result } = renderHook(() => usePortfolio());

    // Open two positions
    act(() => {
      result.current.openPosition({
        asset: "BTC",
        direction: "LONG",
        entryPrice: 65000,
        size: 1,
        capitalAllocated: 50000,
        openedAt: "2024-01-01T00:00:00Z",
      });
    });

    act(() => {
      result.current.openPosition({
        asset: "ETH",
        direction: "LONG",
        entryPrice: 3200,
        size: 5,
        capitalAllocated: 16000,
        openedAt: "2024-01-01T00:00:00Z",
      });
    });

    expect(result.current.state.positions).toHaveLength(2);
    expect(result.current.state.availableCapital).toBe(100_000 - 50000 - 16000);

    // Update prices
    act(() => {
      result.current.updatePrices({ BTC: 66000, ETH: 3100 });
    });

    // BTC unrealized: +1000, ETH unrealized: -500
    expect(result.current.unrealizedPnl).toBe(500);

    // Close only BTC (winner)
    const btcPosId = result.current.state.positions.find(
      (p) => p.asset === "BTC"
    )!.id;

    act(() => {
      result.current.closePosition(btcPosId);
    });

    expect(result.current.state.positions).toHaveLength(1); // ETH remains
    expect(result.current.state.closedTrades).toHaveLength(1);
    expect(result.current.state.realizedPnl).toBe(1000);
    expect(result.current.winRate).toBe(100); // 1 win / 1 trade
  });

  it("tracks peak value and drawdown across price swings", () => {
    const { result } = renderHook(() => usePortfolio());

    act(() => {
      result.current.openPosition({
        asset: "BTC",
        direction: "LONG",
        entryPrice: 65000,
        size: 1,
        capitalAllocated: 65000,
        openedAt: "2024-01-01T00:00:00Z",
      });
    });

    // Price goes up → new peak
    act(() => {
      result.current.updatePrices({ BTC: 70000 });
    });
    // Total value = 35000 (available) + 65000 (allocated) + 5000 (pnl) = 105000
    expect(result.current.totalValue).toBe(105000);
    expect(result.current.state.peakValue).toBe(105000);
    expect(result.current.drawdown).toBe(0);

    // Price drops significantly → drawdown
    act(() => {
      result.current.updatePrices({ BTC: 60000 });
    });
    // Total value = 35000 + 65000 + (-5000) = 95000
    expect(result.current.totalValue).toBe(95000);
    expect(result.current.state.peakValue).toBe(105000); // unchanged
    // Drawdown = (105000 - 95000) / 105000 * 100 ≈ 9.52%
    expect(result.current.drawdown).toBeCloseTo(9.524, 1);
  });

  it("full lifecycle: open → profit → close → open another → loss → close", () => {
    const { result } = renderHook(() => usePortfolio());

    // Trade 1: Win
    act(() => {
      result.current.openPosition({
        asset: "BTC",
        direction: "LONG",
        entryPrice: 60000,
        size: 1,
        capitalAllocated: 60000,
        openedAt: "2024-01-01T00:00:00Z",
      });
    });
    act(() => {
      result.current.updatePrices({ BTC: 62000 });
    });
    act(() => {
      result.current.closePosition(result.current.state.positions[0].id);
    });

    expect(result.current.state.realizedPnl).toBe(2000);

    // Trade 2: Loss
    act(() => {
      result.current.openPosition({
        asset: "ETH",
        direction: "SHORT",
        entryPrice: 3200,
        size: 10,
        capitalAllocated: 32000,
        openedAt: "2024-01-02T00:00:00Z",
      });
    });
    act(() => {
      result.current.updatePrices({ ETH: 3500 });
    });
    act(() => {
      result.current.closePosition(result.current.state.positions[0].id);
    });

    const ethLoss = (3200 - 3500) * 10; // -3000
    expect(result.current.state.realizedPnl).toBe(2000 + ethLoss);
    expect(result.current.state.closedTrades).toHaveLength(2);
    expect(result.current.winRate).toBe(50); // 1 win, 1 loss
    expect(result.current.avgWin).toBe(2000);
    expect(result.current.avgLoss).toBe(ethLoss);
  });

  it("reset clears all state mid-session", () => {
    const { result } = renderHook(() => usePortfolio());

    act(() => {
      result.current.openPosition({
        asset: "BTC",
        direction: "LONG",
        entryPrice: 65000,
        size: 1,
        capitalAllocated: 65000,
        openedAt: "2024-01-01T00:00:00Z",
      });
    });

    act(() => {
      result.current.resetPortfolio(200_000);
    });

    expect(result.current.state.positions).toHaveLength(0);
    expect(result.current.state.totalCapital).toBe(200_000);
    expect(result.current.state.availableCapital).toBe(200_000);
    expect(result.current.state.realizedPnl).toBe(0);
    expect(result.current.state.closedTrades).toHaveLength(0);
  });
});
