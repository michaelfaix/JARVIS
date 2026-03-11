"use client";

import { useCallback, useEffect, useState } from "react";
import type { Position, PortfolioState } from "@/lib/types";
import { loadJSON, saveJSON } from "@/lib/storage";
import { DEFAULT_CAPITAL } from "@/lib/constants";

const KEY = "jarvis-portfolio";

function defaultState(): PortfolioState {
  return {
    totalCapital: DEFAULT_CAPITAL,
    availableCapital: DEFAULT_CAPITAL,
    positions: [],
    realizedPnl: 0,
  };
}

export function usePortfolio() {
  const [state, setState] = useState<PortfolioState>(defaultState);

  useEffect(() => {
    setState(loadJSON(KEY, defaultState()));
  }, []);

  const save = (next: PortfolioState) => {
    setState(next);
    saveJSON(KEY, next);
  };

  const openPosition = useCallback(
    (pos: Omit<Position, "id" | "pnl" | "pnlPercent" | "currentPrice">) => {
      setState((prev) => {
        if (prev.availableCapital < pos.capitalAllocated) return prev;
        const newPos: Position = {
          ...pos,
          id: `${pos.asset}-${Date.now()}`,
          currentPrice: pos.entryPrice,
          pnl: 0,
          pnlPercent: 0,
        };
        const next: PortfolioState = {
          ...prev,
          availableCapital: prev.availableCapital - pos.capitalAllocated,
          positions: [...prev.positions, newPos],
        };
        saveJSON(KEY, next);
        return next;
      });
    },
    []
  );

  const closePosition = useCallback((posId: string) => {
    setState((prev) => {
      const pos = prev.positions.find((p) => p.id === posId);
      if (!pos) return prev;
      const pnl =
        pos.direction === "LONG"
          ? (pos.currentPrice - pos.entryPrice) * pos.size
          : (pos.entryPrice - pos.currentPrice) * pos.size;
      const next: PortfolioState = {
        ...prev,
        availableCapital: prev.availableCapital + pos.capitalAllocated + pnl,
        positions: prev.positions.filter((p) => p.id !== posId),
        realizedPnl: prev.realizedPnl + pnl,
      };
      saveJSON(KEY, next);
      return next;
    });
  }, []);

  const updatePrices = useCallback(
    (prices: Record<string, number>) => {
      setState((prev) => {
        const positions = prev.positions.map((pos) => {
          const currentPrice = prices[pos.asset] ?? pos.currentPrice;
          const rawPnl =
            pos.direction === "LONG"
              ? (currentPrice - pos.entryPrice) * pos.size
              : (pos.entryPrice - currentPrice) * pos.size;
          return {
            ...pos,
            currentPrice,
            pnl: rawPnl,
            pnlPercent:
              pos.capitalAllocated > 0
                ? (rawPnl / pos.capitalAllocated) * 100
                : 0,
          };
        });
        const next = { ...prev, positions };
        saveJSON(KEY, next);
        return next;
      });
    },
    []
  );

  const resetPortfolio = useCallback((capital?: number) => {
    const next = defaultState();
    if (capital) {
      next.totalCapital = capital;
      next.availableCapital = capital;
    }
    save(next);
  }, []);

  const unrealizedPnl = state.positions.reduce((sum, p) => sum + p.pnl, 0);
  const totalValue = state.availableCapital +
    state.positions.reduce((sum, p) => sum + p.capitalAllocated + p.pnl, 0);

  return {
    state,
    openPosition,
    closePosition,
    updatePrices,
    resetPortfolio,
    unrealizedPnl,
    totalValue,
  };
}
