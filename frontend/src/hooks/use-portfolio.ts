"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Position, ClosedTrade, PortfolioState } from "@/lib/types";
import { loadJSON, saveJSON } from "@/lib/storage";
import { DEFAULT_CAPITAL } from "@/lib/constants";
import { createClient } from "@/lib/supabase/client";
import { useAuth } from "@/hooks/use-auth";

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

/**
 * Sanitize loaded state: ensure no position ID appears in both
 * `positions` and `closedTrades` (closed wins).
 */
function sanitize(state: PortfolioState): PortfolioState {
  if (!state.closedTrades) state.closedTrades = [];
  if (!state.peakValue) state.peakValue = state.totalCapital;

  const closedIds = new Set(state.closedTrades.map((t) => t.id));
  const cleanPositions = state.positions.filter((p) => !closedIds.has(p.id));

  if (cleanPositions.length !== state.positions.length) {
    // Recalculate available capital for removed ghost positions
    const removedCapital = state.positions
      .filter((p) => closedIds.has(p.id))
      .reduce((sum, p) => sum + p.capitalAllocated, 0);
    return {
      ...state,
      positions: cleanPositions,
      availableCapital: state.availableCapital + removedCapital,
    };
  }

  return state;
}

export function usePortfolio() {
  const [state, setState] = useState<PortfolioState>(defaultState);
  const { user } = useAuth();
  const supabase = createClient();
  const syncTimer = useRef<ReturnType<typeof setTimeout>>();
  // Track whether this is the initial load (skip persistence on mount)
  const initialLoadDone = useRef(false);

  // ---------------------------------------------------------------------------
  // Persist: write state to localStorage + Supabase
  // Called from a useEffect (NOT inside setState updaters).
  // ---------------------------------------------------------------------------
  const persistToStorage = useCallback(
    (next: PortfolioState, immediate?: boolean) => {
      saveJSON(KEY, next);
      if (!user) return;

      const doSync = () => {
        supabase
          .from("portfolios")
          .upsert({
            user_id: user.id,
            total_capital: next.totalCapital,
            available_capital: next.availableCapital,
            realized_pnl: next.realizedPnl,
            peak_value: next.peakValue,
            positions: JSON.parse(JSON.stringify(next.positions)),
            updated_at: new Date().toISOString(),
          })
          .then(() => {}); // fire-and-forget
      };

      // Always clear any pending debounced sync to prevent stale overwrites
      clearTimeout(syncTimer.current);

      if (immediate) {
        doSync();
      } else {
        syncTimer.current = setTimeout(doSync, 10_000);
      }
    },
    [user, supabase]
  );

  // ---------------------------------------------------------------------------
  // Auto-persist: whenever state changes (after initial load), write to storage.
  // Debounce price-only updates; critical mutations (open/close) set a flag.
  // ---------------------------------------------------------------------------
  const needsImmediateSync = useRef(false);

  useEffect(() => {
    if (!initialLoadDone.current) return; // skip the mount-triggered render
    persistToStorage(state, needsImmediateSync.current);
    needsImmediateSync.current = false;
  }, [state, persistToStorage]);

  // ---------------------------------------------------------------------------
  // Load on mount: try Supabase first, then localStorage
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (!user) {
      const loaded = sanitize(loadJSON(KEY, defaultState()));
      setState(loaded);
      // Save sanitized version back
      saveJSON(KEY, loaded);
      initialLoadDone.current = true;
      return;
    }

    (async () => {
      const { data: portfolio } = await supabase
        .from("portfolios")
        .select("*")
        .eq("user_id", user.id)
        .single();

      const { data: trades } = await supabase
        .from("trades")
        .select("*")
        .eq("user_id", user.id)
        .order("closed_at", { ascending: false })
        .limit(100);

      if (portfolio) {
        const loaded = sanitize({
          totalCapital: Number(portfolio.total_capital),
          availableCapital: Number(portfolio.available_capital),
          realizedPnl: Number(portfolio.realized_pnl),
          peakValue: Number(portfolio.peak_value),
          positions: (portfolio.positions as Position[]) ?? [],
          closedTrades: (trades ?? []).map((t) => ({
            id: t.id,
            asset: t.asset,
            direction: t.direction as "LONG" | "SHORT",
            entryPrice: Number(t.entry_price),
            exitPrice: Number(t.exit_price),
            size: Number(t.size),
            capitalAllocated: Number(t.capital_allocated),
            openedAt: t.opened_at,
            closedAt: t.closed_at,
            pnl: Number(t.pnl),
            pnlPercent: Number(t.pnl_percent),
          })),
        });
        setState(loaded);
        saveJSON(KEY, loaded);
      } else {
        // Migrate localStorage data to Supabase on first login
        const local = sanitize(loadJSON(KEY, defaultState()));
        setState(local);
        persistToStorage(local, true);
      }
      initialLoadDone.current = true;
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id]);

  // ---------------------------------------------------------------------------
  // Actions
  // ---------------------------------------------------------------------------

  const openPosition = useCallback(
    (pos: Omit<Position, "id" | "pnl" | "pnlPercent" | "currentPrice">) => {
      needsImmediateSync.current = true;
      setState((prev) => {
        if (prev.availableCapital < pos.capitalAllocated) return prev;
        const newPos: Position = {
          ...pos,
          id: `${pos.asset}-${Date.now()}`,
          currentPrice: pos.entryPrice,
          pnl: 0,
          pnlPercent: 0,
        };
        return {
          ...prev,
          availableCapital: prev.availableCapital - pos.capitalAllocated,
          positions: [...prev.positions, newPos],
        };
      });
    },
    []
  );

  const closePosition = useCallback(
    (posId: string) => {
      needsImmediateSync.current = true;
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

        // Write closed trade to Supabase (fire-and-forget)
        if (user) {
          supabase
            .from("trades")
            .insert({
              id: closedTrade.id,
              user_id: user.id,
              asset: closedTrade.asset,
              direction: closedTrade.direction,
              entry_price: closedTrade.entryPrice,
              exit_price: closedTrade.exitPrice,
              size: closedTrade.size,
              capital_allocated: closedTrade.capitalAllocated,
              opened_at: closedTrade.openedAt,
              closed_at: closedTrade.closedAt,
              pnl: closedTrade.pnl,
              pnl_percent: closedTrade.pnlPercent,
            })
            .then(() => {});
        }

        return {
          ...prev,
          availableCapital: prev.availableCapital + pos.capitalAllocated + pnl,
          positions: prev.positions.filter((p) => p.id !== posId),
          realizedPnl: prev.realizedPnl + pnl,
          closedTrades: [closedTrade, ...prev.closedTrades],
        };
      });
    },
    [user, supabase]
  );

  const updatePrices = useCallback(
    (prices: Record<string, number>) => {
      setState((prev) => {
        if (prev.positions.length === 0) return prev;
        let changed = false;
        const positions = prev.positions.map((pos) => {
          const currentPrice = prices[pos.asset] ?? pos.currentPrice;
          if (currentPrice === pos.currentPrice) return pos;
          changed = true;
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
        if (!changed) return prev;
        const currentValue =
          prev.availableCapital +
          positions.reduce((s, p) => s + p.capitalAllocated + p.pnl, 0);
        const peakValue = Math.max(prev.peakValue, currentValue);
        return { ...prev, positions, peakValue };
      });
    },
    []
  );

  const resetPortfolio = useCallback(
    (capital?: number) => {
      needsImmediateSync.current = true;
      const next = defaultState();
      if (capital) {
        next.totalCapital = capital;
        next.availableCapital = capital;
        next.peakValue = capital;
      }
      setState(next);
    },
    []
  );

  // ---------------------------------------------------------------------------
  // Computed values
  // ---------------------------------------------------------------------------
  const unrealizedPnl = state.positions.reduce((sum, p) => sum + p.pnl, 0);
  const totalValue =
    state.availableCapital +
    state.positions.reduce((sum, p) => sum + p.capitalAllocated + p.pnl, 0);

  const wins = state.closedTrades.filter((t) => t.pnl > 0);
  const losses = state.closedTrades.filter((t) => t.pnl <= 0);
  const winRate =
    state.closedTrades.length > 0
      ? (wins.length / state.closedTrades.length) * 100
      : 0;
  const avgWin =
    wins.length > 0 ? wins.reduce((s, t) => s + t.pnl, 0) / wins.length : 0;
  const avgLoss =
    losses.length > 0
      ? losses.reduce((s, t) => s + t.pnl, 0) / losses.length
      : 0;
  const drawdown =
    state.peakValue > 0
      ? ((state.peakValue - totalValue) / state.peakValue) * 100
      : 0;
  const maxDrawdownPnl = state.peakValue - totalValue;

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
    winRate,
    avgWin,
    avgLoss,
    drawdown,
    maxDrawdownPnl,
    exposureByAsset,
    maxSingleExposurePct,
  };
}
