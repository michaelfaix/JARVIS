// =============================================================================
// Tests for useAutoSLTP hook
// =============================================================================

import { renderHook, act } from "@testing-library/react";
import { useAutoSLTP } from "@/hooks/use-auto-sl-tp";
import type { Position } from "@/lib/types";

beforeEach(() => {
  localStorage.clear();
});

function makePosition(overrides: Partial<Position> = {}): Position {
  return {
    id: "pos-1",
    asset: "BTCUSD",
    direction: "LONG",
    entryPrice: 40000,
    currentPrice: 40000,
    size: 1,
    capitalAllocated: 40000,
    openedAt: new Date().toISOString(),
    pnl: 0,
    pnlPercent: 0,
    ...overrides,
  };
}

describe("useAutoSLTP", () => {
  const closePositionFn = jest.fn();
  const pushNotificationFn = jest.fn();

  beforeEach(() => {
    closePositionFn.mockClear();
    pushNotificationFn.mockClear();
  });

  // -----------------------------------------------------------------------
  // setSLTP / getSLTP / removeSLTP
  // -----------------------------------------------------------------------

  it("starts with empty SLTP map", () => {
    const pos = makePosition();
    const { result } = renderHook(() =>
      useAutoSLTP([pos], closePositionFn, pushNotificationFn)
    );
    expect(result.current.sltpMap).toEqual({});
  });

  it("setSLTP registers SL/TP for a position", () => {
    const pos = makePosition();
    const { result } = renderHook(() =>
      useAutoSLTP([pos], closePositionFn, pushNotificationFn)
    );

    act(() => {
      result.current.setSLTP("pos-1", "BTCUSD", "LONG", 38000, 45000);
    });

    expect(result.current.sltpMap["pos-1"]).toEqual({
      positionId: "pos-1",
      asset: "BTCUSD",
      direction: "LONG",
      stopLoss: 38000,
      takeProfit: 45000,
    });
  });

  it("getSLTP returns the correct SLTP entry", () => {
    const pos = makePosition();
    const { result } = renderHook(() =>
      useAutoSLTP([pos], closePositionFn, pushNotificationFn)
    );

    act(() => {
      result.current.setSLTP("pos-1", "BTCUSD", "LONG", 38000, 45000);
    });

    const sltp = result.current.getSLTP("pos-1");
    expect(sltp?.stopLoss).toBe(38000);
    expect(sltp?.takeProfit).toBe(45000);
  });

  it("getSLTP returns undefined for unknown position", () => {
    const pos = makePosition();
    const { result } = renderHook(() =>
      useAutoSLTP([pos], closePositionFn, pushNotificationFn)
    );

    expect(result.current.getSLTP("nonexistent")).toBeUndefined();
  });

  it("removeSLTP removes the entry", () => {
    const pos = makePosition();
    const { result } = renderHook(() =>
      useAutoSLTP([pos], closePositionFn, pushNotificationFn)
    );

    act(() => {
      result.current.setSLTP("pos-1", "BTCUSD", "LONG", 38000, 45000);
    });
    act(() => {
      result.current.removeSLTP("pos-1");
    });

    expect(result.current.sltpMap["pos-1"]).toBeUndefined();
  });

  // -----------------------------------------------------------------------
  // LONG position — stop loss
  // -----------------------------------------------------------------------

  it("triggers stop loss for LONG when price <= SL", () => {
    const pos = makePosition({ direction: "LONG" });
    const { result } = renderHook(() =>
      useAutoSLTP([pos], closePositionFn, pushNotificationFn)
    );

    act(() => {
      result.current.setSLTP("pos-1", "BTCUSD", "LONG", 38000, 45000);
    });

    let events: ReturnType<typeof result.current.checkSLTP>;
    act(() => {
      events = result.current.checkSLTP({ BTCUSD: 37500 });
    });

    expect(events!).toHaveLength(1);
    expect(events![0].reason).toBe("stop_loss");
    expect(events![0].triggerPrice).toBe(37500);
    expect(closePositionFn).toHaveBeenCalledWith("pos-1");
    expect(pushNotificationFn).toHaveBeenCalledWith(
      "trade",
      expect.stringContaining("Stop Loss"),
      expect.any(String)
    );
  });

  // -----------------------------------------------------------------------
  // LONG position — take profit
  // -----------------------------------------------------------------------

  it("triggers take profit for LONG when price >= TP", () => {
    const pos = makePosition({ direction: "LONG" });
    const { result } = renderHook(() =>
      useAutoSLTP([pos], closePositionFn, pushNotificationFn)
    );

    act(() => {
      result.current.setSLTP("pos-1", "BTCUSD", "LONG", 38000, 45000);
    });

    let events: ReturnType<typeof result.current.checkSLTP>;
    act(() => {
      events = result.current.checkSLTP({ BTCUSD: 46000 });
    });

    expect(events!).toHaveLength(1);
    expect(events![0].reason).toBe("take_profit");
    expect(closePositionFn).toHaveBeenCalledWith("pos-1");
  });

  // -----------------------------------------------------------------------
  // LONG position — no trigger when price in range
  // -----------------------------------------------------------------------

  it("does not trigger for LONG when price is between SL and TP", () => {
    const pos = makePosition({ direction: "LONG" });
    const { result } = renderHook(() =>
      useAutoSLTP([pos], closePositionFn, pushNotificationFn)
    );

    act(() => {
      result.current.setSLTP("pos-1", "BTCUSD", "LONG", 38000, 45000);
    });

    let events: ReturnType<typeof result.current.checkSLTP>;
    act(() => {
      events = result.current.checkSLTP({ BTCUSD: 41000 });
    });

    expect(events!).toHaveLength(0);
    expect(closePositionFn).not.toHaveBeenCalled();
  });

  // -----------------------------------------------------------------------
  // SHORT position — stop loss
  // -----------------------------------------------------------------------

  it("triggers stop loss for SHORT when price >= SL", () => {
    const pos = makePosition({ id: "pos-2", direction: "SHORT", entryPrice: 40000 });
    const { result } = renderHook(() =>
      useAutoSLTP([pos], closePositionFn, pushNotificationFn)
    );

    act(() => {
      result.current.setSLTP("pos-2", "BTCUSD", "SHORT", 42000, 36000);
    });

    let events: ReturnType<typeof result.current.checkSLTP>;
    act(() => {
      events = result.current.checkSLTP({ BTCUSD: 42500 });
    });

    expect(events!).toHaveLength(1);
    expect(events![0].reason).toBe("stop_loss");
    expect(closePositionFn).toHaveBeenCalledWith("pos-2");
  });

  // -----------------------------------------------------------------------
  // SHORT position — take profit
  // -----------------------------------------------------------------------

  it("triggers take profit for SHORT when price <= TP", () => {
    const pos = makePosition({ id: "pos-3", direction: "SHORT", entryPrice: 40000 });
    const { result } = renderHook(() =>
      useAutoSLTP([pos], closePositionFn, pushNotificationFn)
    );

    act(() => {
      result.current.setSLTP("pos-3", "BTCUSD", "SHORT", 42000, 36000);
    });

    let events: ReturnType<typeof result.current.checkSLTP>;
    act(() => {
      events = result.current.checkSLTP({ BTCUSD: 35000 });
    });

    expect(events!).toHaveLength(1);
    expect(events![0].reason).toBe("take_profit");
  });

  // -----------------------------------------------------------------------
  // SHORT position — no trigger
  // -----------------------------------------------------------------------

  it("does not trigger for SHORT when price is between TP and SL", () => {
    const pos = makePosition({ id: "pos-4", direction: "SHORT", entryPrice: 40000 });
    const { result } = renderHook(() =>
      useAutoSLTP([pos], closePositionFn, pushNotificationFn)
    );

    act(() => {
      result.current.setSLTP("pos-4", "BTCUSD", "SHORT", 42000, 36000);
    });

    let events: ReturnType<typeof result.current.checkSLTP>;
    act(() => {
      events = result.current.checkSLTP({ BTCUSD: 39000 });
    });

    expect(events!).toHaveLength(0);
    expect(closePositionFn).not.toHaveBeenCalled();
  });

  // -----------------------------------------------------------------------
  // Auto-close history
  // -----------------------------------------------------------------------

  it("records auto-close events in history", () => {
    const pos = makePosition();
    const { result } = renderHook(() =>
      useAutoSLTP([pos], closePositionFn, pushNotificationFn)
    );

    act(() => {
      result.current.setSLTP("pos-1", "BTCUSD", "LONG", 38000, 45000);
    });

    act(() => {
      result.current.checkSLTP({ BTCUSD: 37000 });
    });

    expect(result.current.autoCloseHistory).toHaveLength(1);
    expect(result.current.autoCloseHistory[0].reason).toBe("stop_loss");
  });

  // -----------------------------------------------------------------------
  // SLTP removed after trigger
  // -----------------------------------------------------------------------

  it("removes SLTP entry after it triggers", () => {
    const pos = makePosition();
    const { result } = renderHook(() =>
      useAutoSLTP([pos], closePositionFn, pushNotificationFn)
    );

    act(() => {
      result.current.setSLTP("pos-1", "BTCUSD", "LONG", 38000, 45000);
    });

    act(() => {
      result.current.checkSLTP({ BTCUSD: 37000 });
    });

    expect(result.current.sltpMap["pos-1"]).toBeUndefined();
  });

  // -----------------------------------------------------------------------
  // Ignores assets not in price map
  // -----------------------------------------------------------------------

  it("checkSLTP ignores positions without a current price", () => {
    const pos = makePosition({ asset: "BTCUSD" });
    const { result } = renderHook(() =>
      useAutoSLTP([pos], closePositionFn, pushNotificationFn)
    );

    act(() => {
      result.current.setSLTP("pos-1", "BTCUSD", "LONG", 38000, 45000);
    });

    let events: ReturnType<typeof result.current.checkSLTP>;
    act(() => {
      events = result.current.checkSLTP({ ETHUSD: 37000 });
    });

    expect(events!).toHaveLength(0);
  });

  // -----------------------------------------------------------------------
  // Persistence
  // -----------------------------------------------------------------------

  it("persists SLTP map to localStorage", () => {
    const pos = makePosition();
    const { result } = renderHook(() =>
      useAutoSLTP([pos], closePositionFn, pushNotificationFn)
    );

    act(() => {
      result.current.setSLTP("pos-1", "BTCUSD", "LONG", 38000, 45000);
    });

    const stored = JSON.parse(localStorage.getItem("jarvis-sltp")!);
    expect(stored["pos-1"]).toBeDefined();
    expect(stored["pos-1"].stopLoss).toBe(38000);
  });
});
