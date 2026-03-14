// =============================================================================
// Tests: use-portfolio.ts — Portfolio state management
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

describe("usePortfolio", () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  it("initializes with default state", () => {
    const { result } = renderHook(() => usePortfolio());
    expect(result.current.state.totalCapital).toBe(100_000);
    expect(result.current.state.availableCapital).toBe(100_000);
    expect(result.current.state.positions).toHaveLength(0);
    expect(result.current.state.realizedPnl).toBe(0);
    expect(result.current.totalValue).toBe(100_000);
  });

  it("opens a position and deducts capital", () => {
    const { result } = renderHook(() => usePortfolio());

    act(() => {
      result.current.openPosition({
        asset: "BTC",
        direction: "LONG",
        entryPrice: 65000,
        size: 0.1,
        capitalAllocated: 6500,
        openedAt: new Date().toISOString(),
      });
    });

    expect(result.current.state.positions).toHaveLength(1);
    expect(result.current.state.availableCapital).toBe(100_000 - 6500);
    expect(result.current.state.positions[0].asset).toBe("BTC");
    expect(result.current.state.positions[0].direction).toBe("LONG");
    expect(result.current.state.positions[0].pnl).toBe(0);
  });

  it("rejects position if insufficient capital", () => {
    const { result } = renderHook(() => usePortfolio());

    act(() => {
      result.current.openPosition({
        asset: "BTC",
        direction: "LONG",
        entryPrice: 65000,
        size: 10,
        capitalAllocated: 200_000, // > 100k available
        openedAt: new Date().toISOString(),
      });
    });

    expect(result.current.state.positions).toHaveLength(0);
    expect(result.current.state.availableCapital).toBe(100_000);
  });

  it("closes a LONG position with correct P&L", () => {
    const { result } = renderHook(() => usePortfolio());

    // Open position
    act(() => {
      result.current.openPosition({
        asset: "BTC",
        direction: "LONG",
        entryPrice: 65000,
        size: 1,
        capitalAllocated: 65000,
        openedAt: new Date().toISOString(),
      });
    });

    const posId = result.current.state.positions[0].id;

    // Update price to simulate profit
    act(() => {
      result.current.updatePrices({ BTC: 66000 });
    });

    expect(result.current.state.positions[0].pnl).toBe(1000); // (66000 - 65000) * 1

    // Close position
    act(() => {
      result.current.closePosition(posId);
    });

    expect(result.current.state.positions).toHaveLength(0);
    expect(result.current.state.closedTrades).toHaveLength(1);
    // P&L reduced by fees+slippage (~0.2% of capital + ~0.1% slippage)
    expect(result.current.state.closedTrades[0].pnl).toBeGreaterThan(500);
    expect(result.current.state.closedTrades[0].pnl).toBeLessThan(1000);
    expect(result.current.state.realizedPnl).toBeGreaterThan(500);
    expect(result.current.state.availableCapital).toBeGreaterThan(100_000);
  });

  it("closes a SHORT position with correct P&L", () => {
    const { result } = renderHook(() => usePortfolio());

    act(() => {
      result.current.openPosition({
        asset: "ETH",
        direction: "SHORT",
        entryPrice: 3200,
        size: 10,
        capitalAllocated: 32000,
        openedAt: new Date().toISOString(),
      });
    });

    const posId = result.current.state.positions[0].id;

    // Price drops = profit for SHORT
    act(() => {
      result.current.updatePrices({ ETH: 3000 });
    });

    expect(result.current.state.positions[0].pnl).toBe(2000); // (3200 - 3000) * 10

    act(() => {
      result.current.closePosition(posId);
    });

    // P&L reduced by fees+slippage
    expect(result.current.state.closedTrades[0].pnl).toBeGreaterThan(1800);
    expect(result.current.state.closedTrades[0].pnl).toBeLessThan(2000);
    expect(result.current.state.realizedPnl).toBeGreaterThan(1800);
  });

  it("calculates P&L percentage correctly", () => {
    const { result } = renderHook(() => usePortfolio());

    act(() => {
      result.current.openPosition({
        asset: "BTC",
        direction: "LONG",
        entryPrice: 50000,
        size: 1,
        capitalAllocated: 50000,
        openedAt: new Date().toISOString(),
      });
    });

    act(() => {
      result.current.updatePrices({ BTC: 55000 });
    });

    // pnl = 5000, pnlPercent = (5000/50000)*100 = 10%
    expect(result.current.state.positions[0].pnlPercent).toBe(10);
  });

  it("computes win rate from closed trades", () => {
    const { result } = renderHook(() => usePortfolio());

    // Open and close a winning trade
    act(() => {
      result.current.openPosition({
        asset: "BTC",
        direction: "LONG",
        entryPrice: 60000,
        size: 1,
        capitalAllocated: 60000,
        openedAt: new Date().toISOString(),
      });
    });
    act(() => {
      result.current.updatePrices({ BTC: 61000 });
    });
    act(() => {
      result.current.closePosition(result.current.state.positions[0].id);
    });

    // Open and close a losing trade
    act(() => {
      result.current.openPosition({
        asset: "ETH",
        direction: "LONG",
        entryPrice: 3200,
        size: 1,
        capitalAllocated: 3200,
        openedAt: new Date().toISOString(),
      });
    });
    act(() => {
      result.current.updatePrices({ ETH: 3100 });
    });
    act(() => {
      result.current.closePosition(result.current.state.positions[0].id);
    });

    expect(result.current.state.closedTrades).toHaveLength(2);
    expect(result.current.winRate).toBe(50); // 1 win / 2 trades
  });

  it("persists state to localStorage", () => {
    const { result } = renderHook(() => usePortfolio());

    act(() => {
      result.current.openPosition({
        asset: "SOL",
        direction: "LONG",
        entryPrice: 145,
        size: 10,
        capitalAllocated: 1450,
        openedAt: new Date().toISOString(),
      });
    });

    // localStorage.setItem should have been called with portfolio data
    expect(localStorage.setItem).toHaveBeenCalled();
    const calls = (localStorage.setItem as jest.Mock).mock.calls;
    const portfolioCall = calls.find(
      (c: string[]) => c[0] === "jarvis-portfolio"
    );
    expect(portfolioCall).toBeDefined();
  });

  it("resets portfolio to default state", () => {
    const { result } = renderHook(() => usePortfolio());

    act(() => {
      result.current.openPosition({
        asset: "BTC",
        direction: "LONG",
        entryPrice: 65000,
        size: 1,
        capitalAllocated: 65000,
        openedAt: new Date().toISOString(),
      });
    });

    act(() => {
      result.current.resetPortfolio();
    });

    expect(result.current.state.positions).toHaveLength(0);
    expect(result.current.state.availableCapital).toBe(100_000);
    expect(result.current.state.realizedPnl).toBe(0);
  });

  it("resets portfolio with custom capital", () => {
    const { result } = renderHook(() => usePortfolio());

    act(() => {
      result.current.resetPortfolio(50_000);
    });

    expect(result.current.state.totalCapital).toBe(50_000);
    expect(result.current.state.availableCapital).toBe(50_000);
    expect(result.current.state.peakValue).toBe(50_000);
  });

  it("tracks drawdown correctly", () => {
    const { result } = renderHook(() => usePortfolio());

    act(() => {
      result.current.openPosition({
        asset: "BTC",
        direction: "LONG",
        entryPrice: 65000,
        size: 1,
        capitalAllocated: 65000,
        openedAt: new Date().toISOString(),
      });
    });

    // Price goes up → new peak
    act(() => {
      result.current.updatePrices({ BTC: 70000 });
    });

    // Price drops → drawdown
    act(() => {
      result.current.updatePrices({ BTC: 60000 });
    });

    expect(result.current.drawdown).toBeGreaterThan(0);
  });

  it("calculates exposure by asset", () => {
    const { result } = renderHook(() => usePortfolio());

    act(() => {
      result.current.openPosition({
        asset: "BTC",
        direction: "LONG",
        entryPrice: 65000,
        size: 1,
        capitalAllocated: 50000,
        openedAt: new Date().toISOString(),
      });
    });

    expect(result.current.exposureByAsset).toHaveProperty("BTC");
    expect(result.current.maxSingleExposurePct).toBeGreaterThan(0);
  });

  it("ignores close on non-existent position", () => {
    const { result } = renderHook(() => usePortfolio());

    act(() => {
      result.current.closePosition("non-existent-id");
    });

    expect(result.current.state.positions).toHaveLength(0);
    expect(result.current.state.closedTrades).toHaveLength(0);
  });

  it("does not update prices when no positions exist", () => {
    const { result } = renderHook(() => usePortfolio());
    const stateBefore = result.current.state;

    act(() => {
      result.current.updatePrices({ BTC: 70000 });
    });

    // State reference should be the same (no change)
    expect(result.current.state).toBe(stateBefore);
  });
});
