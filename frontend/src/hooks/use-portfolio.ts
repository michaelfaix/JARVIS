"use client";

import { useCallback, useEffect, useState } from "react";
import type { Position, ClosedTrade, PortfolioState } from "@/lib/types";
import { loadJSON, saveJSON } from "@/lib/storage";
import { DEFAULT_CAPITAL } from "@/lib/constants";

const KEY = "jarvis-portfolio";

function defaultState(): PortfolioState {
  return {
    totalCapital: DEFAULT_CAPITAL,
    availableCapital: DEFAULT_CAPITAL,
    positions: [],
    realizedPnl: 0,
    closedTrades: [],
    peakValue: DEFAULT_CAPITAL,
  };
}

export function usePortfolio() {
  const [state, setState] = useState<PortfolioState>(defaultState);

  useEffect(() => {
    const loaded = loadJSON(KEY, defaultState());
    // Migration: add new fields if missing from old localStorage
    if (!loaded.closedTrades) loaded.closedTrades = [];
    if (!loaded.peakValue) loaded.peakValue = loaded.totalCapital;
    setState(loaded);
  }, []);

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
      const pnlPercent =
        pos.capitalAllocated > 0 ? (pnl / pos.capitalAllocated) * 100 : 0;

      const closedTrade: ClosedTrade = {
        id: pos.id,
        asset: pos.asset,
        direction: pos.direction,
        entryPrice: pos.entryPrice,
        exitPrice: pos.currentPrice,
        size: pos.size,
        capitalAllocated: pos.capitalAllocated,
        openedAt: pos.openedAt,
        closedAt: new Date().toISOString(),
        pnl,
        pnlPercent,
      };

      const next: PortfolioState = {
        ...prev,
        availableCapital: prev.availableCapital + pos.capitalAllocated + pnl,
        positions: prev.positions.filter((p) => p.id !== posId),
        realizedPnl: prev.realizedPnl + pnl,
        closedTrades: [closedTrade, ...prev.closedTrades],
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
        const currentValue =
          prev.availableCapital +
          positions.reduce((s, p) => s + p.capitalAllocated + p.pnl, 0);
        const peakValue = Math.max(prev.peakValue, currentValue);
        const next = { ...prev, positions, peakValue };
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
      next.peakValue = capital;
    }
    setState(next);
    saveJSON(KEY, next);
  }, []);

  // Computed values
  const unrealizedPnl = state.positions.reduce((sum, p) => sum + p.pnl, 0);
  const totalValue =
    state.availableCapital +
    state.positions.reduce((sum, p) => sum + p.capitalAllocated + p.pnl, 0);

  // Trade stats
  const wins = state.closedTrades.filter((t) => t.pnl > 0);
  const losses = state.closedTrades.filter((t) => t.pnl <= 0);
  const winRate =
    state.closedTrades.length > 0
      ? (wins.length / state.closedTrades.length) * 100
      : 0;
  const avgWin = wins.length > 0 ? wins.reduce((s, t) => s + t.pnl, 0) / wins.length : 0;
  const avgLoss =
    losses.length > 0
      ? losses.reduce((s, t) => s + t.pnl, 0) / losses.length
      : 0;
  const drawdown =
    state.peakValue > 0
      ? ((state.peakValue - totalValue) / state.peakValue) * 100
      : 0;
  const maxDrawdownPnl = state.peakValue - totalValue;

  // Exposure per asset (as fraction of totalValue)
  const exposureByAsset: Record<string, number> = {};
  for (const pos of state.positions) {
    const val = pos.capitalAllocated + pos.pnl;
    exposureByAsset[pos.asset] = (exposureByAsset[pos.asset] || 0) + val;
  }
  const maxSingleExposure =
    Object.keys(exposureByAsset).length > 0
      ? Math.max(...Object.values(exposureByAsset))
      : 0;
  const maxSingleExposurePct =
    totalValue > 0 ? (maxSingleExposure / totalValue) * 100 : 0;

  return {
    state,
    openPosition,
    closePosition,
    updatePrices,
    resetPortfolio,
    unrealizedPnl,
    totalValue,
    // Stats
    winRate,
    avgWin,
    avgLoss,
    drawdown,
    maxDrawdownPnl,
    exposureByAsset,
    maxSingleExposurePct,
  };
}
