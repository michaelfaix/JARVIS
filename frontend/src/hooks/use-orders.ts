// =============================================================================
// src/hooks/use-orders.ts — Order management hook (limit, stop-limit, market)
// =============================================================================

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { loadJSON, saveJSON } from "@/lib/storage";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type OrderType = "market" | "limit" | "stop_limit";
export type OrderStatus = "pending" | "filled" | "cancelled";

export interface Order {
  id: string;
  asset: string;
  direction: "LONG" | "SHORT";
  type: OrderType;
  limitPrice?: number;
  stopPrice?: number;
  size: number;
  capitalAllocated: number;
  status: OrderStatus;
  createdAt: string;
  /** SL/TP from the signal at order creation time */
  stopLoss?: number;
  takeProfit?: number;
}

export type NewOrder = Omit<Order, "id" | "status" | "createdAt">;

// ---------------------------------------------------------------------------
// Storage key
// ---------------------------------------------------------------------------

const KEY = "jarvis-orders";

function loadOrders(): Order[] {
  return loadJSON<Order[]>(KEY, []);
}

function persistOrders(orders: Order[]) {
  saveJSON(KEY, orders);
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useOrders(
  openPositionFn: (pos: {
    asset: string;
    direction: "LONG" | "SHORT";
    entryPrice: number;
    size: number;
    capitalAllocated: number;
    openedAt: string;
  }) => void
) {
  const [orders, setOrders] = useState<Order[]>(loadOrders);
  const ordersRef = useRef(orders);
  ordersRef.current = orders;

  // Persist whenever orders change
  useEffect(() => {
    persistOrders(orders);
  }, [orders]);

  // Place a new order
  const placeOrder = useCallback(
    (newOrder: NewOrder): Order => {
      const order: Order = {
        ...newOrder,
        id: `ord-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
        status: "pending",
        createdAt: new Date().toISOString(),
      };

      // Market orders fill immediately — caller should provide the current price
      if (newOrder.type === "market") {
        order.status = "filled";
        openPositionFn({
          asset: newOrder.asset,
          direction: newOrder.direction,
          entryPrice: newOrder.limitPrice ?? 0,
          size: newOrder.size,
          capitalAllocated: newOrder.capitalAllocated,
          openedAt: new Date().toISOString(),
        });
      }

      setOrders((prev) => [order, ...prev]);
      return order;
    },
    [openPositionFn]
  );

  // Cancel a pending order
  const cancelOrder = useCallback((id: string) => {
    setOrders((prev) =>
      prev.map((o) => (o.id === id && o.status === "pending" ? { ...o, status: "cancelled" as const } : o))
    );
  }, []);

  // Check pending limit / stop-limit orders against current prices.
  // Returns array of orders that were just filled.
  const checkOrders = useCallback(
    (prices: Record<string, number>): Order[] => {
      const filled: Order[] = [];

      setOrders((prev) => {
        const next = prev.map((order) => {
          if (order.status !== "pending") return order;

          const currentPrice = prices[order.asset];
          if (currentPrice == null) return order;

          let shouldFill = false;

          if (order.type === "limit") {
            // Limit buy (LONG): fill when price <= limitPrice
            // Limit sell (SHORT): fill when price >= limitPrice
            if (order.direction === "LONG" && order.limitPrice != null && currentPrice <= order.limitPrice) {
              shouldFill = true;
            }
            if (order.direction === "SHORT" && order.limitPrice != null && currentPrice >= order.limitPrice) {
              shouldFill = true;
            }
          }

          if (order.type === "stop_limit") {
            // Stop-limit: stop triggers first, then limit.
            // Simplified: if price passes stop AND limit is met, fill.
            // LONG stop-limit: stop above current, once price >= stopPrice and <= limitPrice
            // SHORT stop-limit: stop below current, once price <= stopPrice and >= limitPrice
            if (
              order.direction === "LONG" &&
              order.stopPrice != null &&
              order.limitPrice != null &&
              currentPrice >= order.stopPrice &&
              currentPrice <= order.limitPrice
            ) {
              shouldFill = true;
            }
            if (
              order.direction === "SHORT" &&
              order.stopPrice != null &&
              order.limitPrice != null &&
              currentPrice <= order.stopPrice &&
              currentPrice >= order.limitPrice
            ) {
              shouldFill = true;
            }
          }

          if (shouldFill) {
            const filledOrder: Order = { ...order, status: "filled" };
            filled.push(filledOrder);

            // Open position at the current market price
            openPositionFn({
              asset: order.asset,
              direction: order.direction,
              entryPrice: currentPrice,
              size: order.size,
              capitalAllocated: order.capitalAllocated,
              openedAt: new Date().toISOString(),
            });

            return filledOrder;
          }

          return order;
        });
        return next;
      });

      return filled;
    },
    [openPositionFn]
  );

  // Remove cancelled/filled orders older than 24h
  const cleanupOrders = useCallback(() => {
    const cutoff = Date.now() - 24 * 60 * 60 * 1000;
    setOrders((prev) =>
      prev.filter(
        (o) => o.status === "pending" || new Date(o.createdAt).getTime() > cutoff
      )
    );
  }, []);

  const pendingOrders = orders.filter((o) => o.status === "pending");
  const filledOrders = orders.filter((o) => o.status === "filled");
  const cancelledOrders = orders.filter((o) => o.status === "cancelled");

  return {
    orders,
    pendingOrders,
    filledOrders,
    cancelledOrders,
    placeOrder,
    cancelOrder,
    checkOrders,
    cleanupOrders,
  };
}
