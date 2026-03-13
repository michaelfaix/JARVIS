// =============================================================================
// src/context/trading-engine-context.tsx — Trading Engine Provider
//
// Provides the central trading engine (portfolio + orders + SL/TP) to all
// pages via React Context. Initialized once in the app layout with live prices.
// =============================================================================

"use client";

import { createContext, useContext, type ReactNode } from "react";
import { useTradingEngine } from "@/hooks/use-trading-engine";
import { usePrices } from "@/hooks/use-prices";

type TradingEngineReturn = ReturnType<typeof useTradingEngine>;
type PricesReturn = ReturnType<typeof usePrices>;

interface TradingEngineContextValue extends TradingEngineReturn {
  prices: PricesReturn["prices"];
  priceHistory: PricesReturn["priceHistory"];
  binanceConnected: PricesReturn["binanceConnected"];
  wsConnected: PricesReturn["wsConnected"];
  quotesConnected: PricesReturn["quotesConnected"];
}

const TradingEngineContext = createContext<TradingEngineContextValue | null>(null);

export function TradingEngineProvider({ children }: { children: ReactNode }) {
  const { prices, priceHistory, binanceConnected, wsConnected, quotesConnected } =
    usePrices(5000);
  const engine = useTradingEngine(prices);

  return (
    <TradingEngineContext.Provider
      value={{
        ...engine,
        prices,
        priceHistory,
        binanceConnected,
        wsConnected,
        quotesConnected,
      }}
    >
      {children}
    </TradingEngineContext.Provider>
  );
}

export function useTradingContext(): TradingEngineContextValue {
  const ctx = useContext(TradingEngineContext);
  if (!ctx) {
    throw new Error("useTradingContext must be used within TradingEngineProvider");
  }
  return ctx;
}
