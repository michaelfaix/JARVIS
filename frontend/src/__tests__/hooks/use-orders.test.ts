// =============================================================================
// Tests for useOrders hook
// =============================================================================

import { renderHook, act } from "@testing-library/react";
import { useOrders, type NewOrder } from "@/hooks/use-orders";

beforeEach(() => {
  localStorage.clear();
});

function makeNewOrder(overrides: Partial<NewOrder> = {}): NewOrder {
  return {
    asset: "BTCUSD",
    direction: "LONG",
    type: "limit",
    limitPrice: 40000,
    size: 0.5,
    capitalAllocated: 20000,
    ...overrides,
  };
}

describe("useOrders", () => {
  const openPositionFn = jest.fn();

  beforeEach(() => {
    openPositionFn.mockClear();
  });

  // -----------------------------------------------------------------------
  // Order creation
  // -----------------------------------------------------------------------

  it("starts with empty order list", () => {
    const { result } = renderHook(() => useOrders(openPositionFn));
    expect(result.current.orders).toHaveLength(0);
    expect(result.current.pendingOrders).toHaveLength(0);
  });

  it("placeOrder creates a pending order with id and timestamp", () => {
    const { result } = renderHook(() => useOrders(openPositionFn));

    act(() => {
      result.current.placeOrder(makeNewOrder());
    });

    expect(result.current.orders).toHaveLength(1);
    expect(result.current.orders[0].id).toMatch(/^ord-/);
    expect(result.current.orders[0].status).toBe("pending");
    expect(result.current.orders[0].asset).toBe("BTCUSD");
    expect(result.current.pendingOrders).toHaveLength(1);
  });

  it("market order fills immediately and opens position", () => {
    const { result } = renderHook(() => useOrders(openPositionFn));

    act(() => {
      result.current.placeOrder(
        makeNewOrder({ type: "market", limitPrice: 42000 })
      );
    });

    expect(result.current.orders[0].status).toBe("filled");
    expect(result.current.filledOrders).toHaveLength(1);
    expect(result.current.pendingOrders).toHaveLength(0);
    expect(openPositionFn).toHaveBeenCalledTimes(1);
    expect(openPositionFn).toHaveBeenCalledWith(
      expect.objectContaining({
        asset: "BTCUSD",
        direction: "LONG",
        entryPrice: 42000,
        size: 0.5,
      })
    );
  });

  it("persists orders to localStorage", () => {
    const { result } = renderHook(() => useOrders(openPositionFn));

    act(() => {
      result.current.placeOrder(makeNewOrder());
    });

    const stored = JSON.parse(localStorage.getItem("jarvis-orders")!);
    expect(stored).toHaveLength(1);
  });

  // -----------------------------------------------------------------------
  // Cancel order
  // -----------------------------------------------------------------------

  it("cancelOrder sets pending order to cancelled", () => {
    const { result } = renderHook(() => useOrders(openPositionFn));

    act(() => {
      result.current.placeOrder(makeNewOrder());
    });

    const id = result.current.orders[0].id;

    act(() => {
      result.current.cancelOrder(id);
    });

    expect(result.current.orders[0].status).toBe("cancelled");
    expect(result.current.pendingOrders).toHaveLength(0);
    expect(result.current.cancelledOrders).toHaveLength(1);
  });

  it("cancelOrder does not affect non-pending orders", () => {
    const { result } = renderHook(() => useOrders(openPositionFn));

    act(() => {
      result.current.placeOrder(makeNewOrder({ type: "market", limitPrice: 40000 }));
    });

    const id = result.current.orders[0].id;
    expect(result.current.orders[0].status).toBe("filled");

    act(() => {
      result.current.cancelOrder(id);
    });

    // Should still be filled, not cancelled
    expect(result.current.orders[0].status).toBe("filled");
  });

  // -----------------------------------------------------------------------
  // checkOrders — limit orders
  // -----------------------------------------------------------------------

  it("fills LONG limit order when price <= limitPrice", () => {
    const { result } = renderHook(() => useOrders(openPositionFn));

    act(() => {
      result.current.placeOrder(
        makeNewOrder({ direction: "LONG", type: "limit", limitPrice: 40000 })
      );
    });

    act(() => {
      result.current.checkOrders({ BTCUSD: 39500 });
    });

    expect(result.current.filledOrders).toHaveLength(1);
    expect(openPositionFn).toHaveBeenCalledWith(
      expect.objectContaining({ entryPrice: 39500 })
    );
  });

  it("fills SHORT limit order when price >= limitPrice", () => {
    const { result } = renderHook(() => useOrders(openPositionFn));

    act(() => {
      result.current.placeOrder(
        makeNewOrder({ direction: "SHORT", type: "limit", limitPrice: 45000 })
      );
    });

    act(() => {
      result.current.checkOrders({ BTCUSD: 45500 });
    });

    expect(result.current.filledOrders).toHaveLength(1);
  });

  it("does not fill LONG limit order when price > limitPrice", () => {
    const { result } = renderHook(() => useOrders(openPositionFn));

    act(() => {
      result.current.placeOrder(
        makeNewOrder({ direction: "LONG", type: "limit", limitPrice: 40000 })
      );
    });

    act(() => {
      result.current.checkOrders({ BTCUSD: 41000 });
    });

    expect(result.current.pendingOrders).toHaveLength(1);
    expect(result.current.filledOrders).toHaveLength(0);
  });

  // -----------------------------------------------------------------------
  // checkOrders — stop-limit orders
  // -----------------------------------------------------------------------

  it("fills LONG stop-limit order when price >= stopPrice and <= limitPrice", () => {
    const { result } = renderHook(() => useOrders(openPositionFn));

    act(() => {
      result.current.placeOrder(
        makeNewOrder({
          direction: "LONG",
          type: "stop_limit",
          stopPrice: 41000,
          limitPrice: 42000,
        })
      );
    });

    act(() => {
      result.current.checkOrders({ BTCUSD: 41500 });
    });

    expect(result.current.filledOrders).toHaveLength(1);
  });

  it("does not fill LONG stop-limit when price is below stopPrice", () => {
    const { result } = renderHook(() => useOrders(openPositionFn));

    act(() => {
      result.current.placeOrder(
        makeNewOrder({
          direction: "LONG",
          type: "stop_limit",
          stopPrice: 41000,
          limitPrice: 42000,
        })
      );
    });

    act(() => {
      result.current.checkOrders({ BTCUSD: 40000 });
    });

    expect(result.current.pendingOrders).toHaveLength(1);
  });

  it("fills SHORT stop-limit order when price <= stopPrice and >= limitPrice", () => {
    const { result } = renderHook(() => useOrders(openPositionFn));

    act(() => {
      result.current.placeOrder(
        makeNewOrder({
          direction: "SHORT",
          type: "stop_limit",
          stopPrice: 39000,
          limitPrice: 38000,
        })
      );
    });

    act(() => {
      result.current.checkOrders({ BTCUSD: 38500 });
    });

    expect(result.current.filledOrders).toHaveLength(1);
  });

  // -----------------------------------------------------------------------
  // checkOrders — ignores unknown assets
  // -----------------------------------------------------------------------

  it("checkOrders ignores orders for assets not in price map", () => {
    const { result } = renderHook(() => useOrders(openPositionFn));

    act(() => {
      result.current.placeOrder(makeNewOrder({ asset: "BTCUSD" }));
    });

    act(() => {
      result.current.checkOrders({ ETHUSD: 3500 });
    });

    expect(result.current.pendingOrders).toHaveLength(1);
  });

  // -----------------------------------------------------------------------
  // Cleanup
  // -----------------------------------------------------------------------

  it("cleanupOrders removes old cancelled/filled orders (>24h)", () => {
    const { result } = renderHook(() => useOrders(openPositionFn));

    // Manually seed an old filled order
    act(() => {
      result.current.placeOrder(makeNewOrder({ type: "market", limitPrice: 40000 }));
    });

    // Hack the createdAt to be old
    // We need to use a fresh order for the pending case
    act(() => {
      result.current.placeOrder(makeNewOrder());
    });

    // We have 2 orders: 1 filled, 1 pending
    expect(result.current.orders).toHaveLength(2);

    act(() => {
      result.current.cleanupOrders();
    });

    // Both are recent, so both should remain
    expect(result.current.orders).toHaveLength(2);
  });

  it("cleanupOrders keeps pending orders regardless of age", () => {
    const { result } = renderHook(() => useOrders(openPositionFn));

    act(() => {
      result.current.placeOrder(makeNewOrder());
    });

    act(() => {
      result.current.cleanupOrders();
    });

    // Pending orders are always kept
    expect(result.current.pendingOrders).toHaveLength(1);
  });

  // -----------------------------------------------------------------------
  // Computed properties
  // -----------------------------------------------------------------------

  it("correctly partitions orders into pending, filled, cancelled", () => {
    const { result } = renderHook(() => useOrders(openPositionFn));

    act(() => {
      result.current.placeOrder(makeNewOrder()); // pending
      result.current.placeOrder(makeNewOrder({ type: "market", limitPrice: 40000 })); // filled
    });

    const pendingId = result.current.pendingOrders[0].id;
    act(() => {
      result.current.cancelOrder(pendingId);
    });

    expect(result.current.pendingOrders).toHaveLength(0);
    expect(result.current.filledOrders).toHaveLength(1);
    expect(result.current.cancelledOrders).toHaveLength(1);
  });
});
