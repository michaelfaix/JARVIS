// =============================================================================
// src/hooks/use-trading-engine.ts — Central Paper Trading Execution Engine
//
// Combines portfolio, orders, and auto SL/TP into one execution loop.
// Runs every second: updates position prices, checks pending orders,
// checks SL/TP triggers. Use this in the app layout so the engine runs
// on every page, not just the signals page.
// =============================================================================

"use client";

import { useEffect, useRef } from "react";
import { usePortfolio } from "@/hooks/use-portfolio";
import { useOrders } from "@/hooks/use-orders";
import { useAutoSLTP } from "@/hooks/use-auto-sl-tp";
import { useNotifications } from "@/hooks/use-notifications";

const ENGINE_TICK_MS = 1000; // 1s tick

export function useTradingEngine(prices: Record<string, number>) {
  const portfolio = usePortfolio();
  const { openPosition, closePosition, updatePrices } = portfolio;

  const orderHook = useOrders(openPosition);
  const { checkOrders, cleanupOrders } = orderHook;

  const { push: pushNotification } = useNotifications();

  const sltpHook = useAutoSLTP(
    portfolio.state.positions,
    closePosition,
    pushNotification
  );
  const { checkSLTP } = sltpHook;

  // Use ref to always have latest prices without re-creating the interval
  const pricesRef = useRef(prices);
  pricesRef.current = prices;

  // Central execution loop — runs every 1s
  useEffect(() => {
    const tick = () => {
      const p = pricesRef.current;
      if (Object.keys(p).length === 0) return;

      // 1. Update position P&L with latest prices
      updatePrices(p);

      // 2. Check pending limit/stop-limit orders for fills
      checkOrders(p);

      // 3. Check SL/TP triggers → auto-close positions
      checkSLTP(p);
    };

    tick(); // Run immediately
    const id = setInterval(tick, ENGINE_TICK_MS);
    return () => clearInterval(id);
  }, [updatePrices, checkOrders, checkSLTP]);

  // Cleanup old filled/cancelled orders every 5 minutes
  useEffect(() => {
    const id = setInterval(cleanupOrders, 5 * 60 * 1000);
    return () => clearInterval(id);
  }, [cleanupOrders]);

  return {
    ...portfolio,
    ...orderHook,
    ...sltpHook,
  };
}
