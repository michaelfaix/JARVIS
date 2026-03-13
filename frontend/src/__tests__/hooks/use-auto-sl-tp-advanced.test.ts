// =============================================================================
// Tests: use-auto-sl-tp.ts — Auto Stop-Loss / Take-Profit execution (advanced)
// =============================================================================

import { renderHook, act } from "@testing-library/react";
import { useAutoSLTP } from "@/hooks/use-auto-sl-tp";
import type { Position } from "@/lib/types";

function makePosition(overrides?: Partial<Position>): Position {
  return {
    id: `pos-${Date.now()}-${Math.random()}`,
    asset: "BTC",
    direction: "LONG",
    entryPrice: 65000,
    currentPrice: 65000,
    size: 1,
    capitalAllocated: 65000,
    openedAt: "2024-01-01T00:00:00Z",
    pnl: 0,
    pnlPercent: 0,
    ...overrides,
  };
}

describe("useAutoSLTP — advanced scenarios", () => {
  let closePositionFn: jest.Mock;
  let pushNotificationFn: jest.Mock;

  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
    closePositionFn = jest.fn();
    pushNotificationFn = jest.fn();
  });

  it("setSLTP registers SL/TP for a position", () => {
    const pos = makePosition({ id: "pos-1" });
    const { result } = renderHook(() =>
      useAutoSLTP([pos], closePositionFn, pushNotificationFn)
    );

    act(() => {
      result.current.setSLTP("pos-1", "BTC", "LONG", 60000, 70000);
    });

    const sltp = result.current.getSLTP("pos-1");
    expect(sltp).toBeDefined();
    expect(sltp!.stopLoss).toBe(60000);
    expect(sltp!.takeProfit).toBe(70000);
  });

  it("removeSLTP clears SL/TP for a position", () => {
    const pos = makePosition({ id: "pos-1" });
    const { result } = renderHook(() =>
      useAutoSLTP([pos], closePositionFn, pushNotificationFn)
    );

    act(() => {
      result.current.setSLTP("pos-1", "BTC", "LONG", 60000, 70000);
    });

    act(() => {
      result.current.removeSLTP("pos-1");
    });

    expect(result.current.getSLTP("pos-1")).toBeUndefined();
  });

  it("triggers stop loss for LONG when price drops below SL", () => {
    const pos = makePosition({ id: "pos-1", direction: "LONG" });
    const { result } = renderHook(() =>
      useAutoSLTP([pos], closePositionFn, pushNotificationFn)
    );

    act(() => {
      result.current.setSLTP("pos-1", "BTC", "LONG", 60000, 70000);
    });

    let events: ReturnType<typeof result.current.checkSLTP>;
    act(() => {
      events = result.current.checkSLTP({ BTC: 59000 });
    });

    expect(closePositionFn).toHaveBeenCalledWith("pos-1");
    expect(pushNotificationFn).toHaveBeenCalled();
    expect(events!).toHaveLength(1);
    expect(events![0].reason).toBe("stop_loss");
  });

  it("triggers take profit for LONG when price rises above TP", () => {
    const pos = makePosition({ id: "pos-1", direction: "LONG" });
    const { result } = renderHook(() =>
      useAutoSLTP([pos], closePositionFn, pushNotificationFn)
    );

    act(() => {
      result.current.setSLTP("pos-1", "BTC", "LONG", 60000, 70000);
    });

    let events: ReturnType<typeof result.current.checkSLTP>;
    act(() => {
      events = result.current.checkSLTP({ BTC: 71000 });
    });

    expect(closePositionFn).toHaveBeenCalledWith("pos-1");
    expect(events!).toHaveLength(1);
    expect(events![0].reason).toBe("take_profit");
  });

  it("triggers stop loss for SHORT when price rises above SL", () => {
    const pos = makePosition({
      id: "pos-2",
      direction: "SHORT",
      entryPrice: 65000,
    });
    const { result } = renderHook(() =>
      useAutoSLTP([pos], closePositionFn, pushNotificationFn)
    );

    act(() => {
      result.current.setSLTP("pos-2", "BTC", "SHORT", 68000, 60000);
    });

    let events: ReturnType<typeof result.current.checkSLTP>;
    act(() => {
      events = result.current.checkSLTP({ BTC: 69000 });
    });

    expect(closePositionFn).toHaveBeenCalledWith("pos-2");
    expect(events!).toHaveLength(1);
    expect(events![0].reason).toBe("stop_loss");
  });

  it("triggers take profit for SHORT when price drops below TP", () => {
    const pos = makePosition({
      id: "pos-2",
      direction: "SHORT",
      entryPrice: 65000,
    });
    const { result } = renderHook(() =>
      useAutoSLTP([pos], closePositionFn, pushNotificationFn)
    );

    act(() => {
      result.current.setSLTP("pos-2", "BTC", "SHORT", 68000, 60000);
    });

    let events: ReturnType<typeof result.current.checkSLTP>;
    act(() => {
      events = result.current.checkSLTP({ BTC: 59000 });
    });

    expect(closePositionFn).toHaveBeenCalledWith("pos-2");
    expect(events!).toHaveLength(1);
    expect(events![0].reason).toBe("take_profit");
  });

  it("does not trigger when price is between SL and TP", () => {
    const pos = makePosition({ id: "pos-1", direction: "LONG" });
    const { result } = renderHook(() =>
      useAutoSLTP([pos], closePositionFn, pushNotificationFn)
    );

    act(() => {
      result.current.setSLTP("pos-1", "BTC", "LONG", 60000, 70000);
    });

    let events: ReturnType<typeof result.current.checkSLTP>;
    act(() => {
      events = result.current.checkSLTP({ BTC: 65000 });
    });

    expect(closePositionFn).not.toHaveBeenCalled();
    expect(events!).toHaveLength(0);
  });

  it("records auto-close events in history", () => {
    const pos = makePosition({ id: "pos-1", direction: "LONG" });
    const { result } = renderHook(() =>
      useAutoSLTP([pos], closePositionFn, pushNotificationFn)
    );

    act(() => {
      result.current.setSLTP("pos-1", "BTC", "LONG", 60000, 70000);
    });

    act(() => {
      result.current.checkSLTP({ BTC: 59000 });
    });

    expect(result.current.autoCloseHistory).toHaveLength(1);
    expect(result.current.autoCloseHistory[0].reason).toBe("stop_loss");
    expect(result.current.autoCloseHistory[0].asset).toBe("BTC");
  });

  it("ignores positions without registered SL/TP", () => {
    const pos = makePosition({ id: "pos-1" });
    const { result } = renderHook(() =>
      useAutoSLTP([pos], closePositionFn, pushNotificationFn)
    );

    // No setSLTP call

    let events: ReturnType<typeof result.current.checkSLTP>;
    act(() => {
      events = result.current.checkSLTP({ BTC: 59000 });
    });

    expect(closePositionFn).not.toHaveBeenCalled();
    expect(events!).toHaveLength(0);
  });

  it("persists SL/TP map to localStorage", () => {
    const pos = makePosition({ id: "pos-1" });
    const { result } = renderHook(() =>
      useAutoSLTP([pos], closePositionFn, pushNotificationFn)
    );

    act(() => {
      result.current.setSLTP("pos-1", "BTC", "LONG", 60000, 70000);
    });

    expect(localStorage.setItem).toHaveBeenCalledWith(
      "jarvis-sltp",
      expect.any(String)
    );
  });
});
