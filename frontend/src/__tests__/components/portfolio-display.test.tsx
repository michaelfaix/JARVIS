// =============================================================================
// Tests: Portfolio P&L display logic (unit tests for computed values)
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

jest.mock("@/hooks/use-auth", () => ({
  useAuth: () => ({ user: null, loading: false, signOut: jest.fn() }),
}));

describe("Portfolio P&L Display Values", () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  it("shows correct unrealized P&L across multiple positions", () => {
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
      result.current.openPosition({
        asset: "ETH",
        direction: "SHORT",
        entryPrice: 3200,
        size: 10,
        capitalAllocated: 5000,
        openedAt: new Date().toISOString(),
      });
    });

    act(() => {
      result.current.updatePrices({ BTC: 66000, ETH: 3100 });
    });

    // BTC LONG: (66000-65000)*1 = +1000
    // ETH SHORT: (3200-3100)*10 = +1000
    expect(result.current.unrealizedPnl).toBe(2000);
  });

  it("calculates total portfolio value correctly", () => {
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
      result.current.updatePrices({ BTC: 67000 });
    });

    // totalValue = availableCapital + (capitalAllocated + pnl)
    // = 35000 + (65000 + 2000) = 102000
    expect(result.current.totalValue).toBe(102000);
  });

  it("computes average win and average loss", () => {
    const { result } = renderHook(() => usePortfolio());

    // Win: +1000
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

    // Win: +2000
    act(() => {
      result.current.openPosition({
        asset: "ETH",
        direction: "LONG",
        entryPrice: 3000,
        size: 1,
        capitalAllocated: 3000,
        openedAt: new Date().toISOString(),
      });
    });
    act(() => {
      result.current.updatePrices({ ETH: 5000 });
    });
    act(() => {
      result.current.closePosition(result.current.state.positions[0].id);
    });

    // Loss: -500
    act(() => {
      result.current.openPosition({
        asset: "SOL",
        direction: "LONG",
        entryPrice: 150,
        size: 10,
        capitalAllocated: 1500,
        openedAt: new Date().toISOString(),
      });
    });
    act(() => {
      result.current.updatePrices({ SOL: 100 });
    });
    act(() => {
      result.current.closePosition(result.current.state.positions[0].id);
    });

    expect(result.current.avgWin).toBe(1500); // (1000 + 2000) / 2
    expect(result.current.avgLoss).toBe(-500); // -500 / 1
    expect(result.current.winRate).toBeCloseTo(66.67, 0); // 2/3
  });

  it("computes maxSingleExposurePct correctly", () => {
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

    act(() => {
      result.current.openPosition({
        asset: "ETH",
        direction: "LONG",
        entryPrice: 3200,
        size: 5,
        capitalAllocated: 10000,
        openedAt: new Date().toISOString(),
      });
    });

    // BTC exposure = 50000, ETH exposure = 10000
    // totalValue = 40000 + 50000 + 10000 = 100000
    // maxSingleExposurePct = (50000/100000)*100 = 50%
    expect(result.current.maxSingleExposurePct).toBe(50);
  });

  it("handles losing SHORT position P&L correctly", () => {
    const { result } = renderHook(() => usePortfolio());

    act(() => {
      result.current.openPosition({
        asset: "BTC",
        direction: "SHORT",
        entryPrice: 65000,
        size: 1,
        capitalAllocated: 65000,
        openedAt: new Date().toISOString(),
      });
    });

    // Price goes up = loss for SHORT
    act(() => {
      result.current.updatePrices({ BTC: 68000 });
    });

    // PnL = (65000 - 68000) * 1 = -3000
    expect(result.current.state.positions[0].pnl).toBe(-3000);
    expect(result.current.unrealizedPnl).toBe(-3000);
  });
});
