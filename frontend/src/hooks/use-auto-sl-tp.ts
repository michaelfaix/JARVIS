// =============================================================================
// src/hooks/use-auto-sl-tp.ts — Auto Stop-Loss / Take-Profit execution
// =============================================================================

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { loadJSON, saveJSON } from "@/lib/storage";
import type { Position } from "@/lib/types";
import type { NotificationType } from "@/hooks/use-notifications";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface PositionSLTP {
  positionId: string;
  asset: string;
  direction: "LONG" | "SHORT";
  stopLoss: number;
  takeProfit: number;
}

export interface AutoCloseEvent {
  id: string;
  positionId: string;
  asset: string;
  direction: "LONG" | "SHORT";
  reason: "stop_loss" | "take_profit";
  triggerPrice: number;
  timestamp: string;
}

// ---------------------------------------------------------------------------
// Storage
// ---------------------------------------------------------------------------

const SLTP_KEY = "jarvis-sltp";
const AUTOCLOSE_KEY = "jarvis-autoclose-history";

function loadSLTP(): Record<string, PositionSLTP> {
  return loadJSON<Record<string, PositionSLTP>>(SLTP_KEY, {});
}

function saveSLTP(data: Record<string, PositionSLTP>) {
  saveJSON(SLTP_KEY, data);
}

function loadAutoCloseHistory(): AutoCloseEvent[] {
  return loadJSON<AutoCloseEvent[]>(AUTOCLOSE_KEY, []);
}

function saveAutoCloseHistory(events: AutoCloseEvent[]) {
  saveJSON(AUTOCLOSE_KEY, events.slice(0, 50));
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useAutoSLTP(
  positions: Position[],
  closePositionFn: (posId: string) => void,
  pushNotificationFn: (type: NotificationType, title: string, message: string) => void
) {
  const [sltpMap, setSltpMap] = useState<Record<string, PositionSLTP>>(loadSLTP);
  const [autoCloseHistory, setAutoCloseHistory] = useState<AutoCloseEvent[]>(loadAutoCloseHistory);
  const sltpRef = useRef(sltpMap);
  sltpRef.current = sltpMap;

  // Persist SLTP whenever it changes
  useEffect(() => {
    saveSLTP(sltpMap);
  }, [sltpMap]);

  // Persist auto-close history
  useEffect(() => {
    saveAutoCloseHistory(autoCloseHistory);
  }, [autoCloseHistory]);

  // Register SL/TP for a position
  const setSLTP = useCallback(
    (positionId: string, asset: string, direction: "LONG" | "SHORT", stopLoss: number, takeProfit: number) => {
      setSltpMap((prev) => ({
        ...prev,
        [positionId]: { positionId, asset, direction, stopLoss, takeProfit },
      }));
    },
    []
  );

  // Remove SL/TP for a position
  const removeSLTP = useCallback((positionId: string) => {
    setSltpMap((prev) => {
      const next = { ...prev };
      delete next[positionId];
      return next;
    });
  }, []);

  // Get SL/TP for a specific position
  const getSLTP = useCallback(
    (positionId: string): PositionSLTP | undefined => {
      return sltpRef.current[positionId];
    },
    []
  );

  // Check positions against current prices for SL/TP hits.
  // Returns array of auto-close events that just fired.
  const checkSLTP = useCallback(
    (prices: Record<string, number>): AutoCloseEvent[] => {
      const events: AutoCloseEvent[] = [];
      const currentSLTP = sltpRef.current;

      for (const pos of positions) {
        const sltp = currentSLTP[pos.id];
        if (!sltp) continue;

        const currentPrice = prices[pos.asset];
        if (currentPrice == null) continue;

        let reason: "stop_loss" | "take_profit" | null = null;

        if (pos.direction === "LONG") {
          if (currentPrice <= sltp.stopLoss) reason = "stop_loss";
          else if (currentPrice >= sltp.takeProfit) reason = "take_profit";
        } else {
          // SHORT: SL is above entry, TP is below entry
          if (currentPrice >= sltp.stopLoss) reason = "stop_loss";
          else if (currentPrice <= sltp.takeProfit) reason = "take_profit";
        }

        if (reason) {
          const event: AutoCloseEvent = {
            id: `ac-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
            positionId: pos.id,
            asset: pos.asset,
            direction: pos.direction,
            reason,
            triggerPrice: currentPrice,
            timestamp: new Date().toISOString(),
          };
          events.push(event);

          // Close the position
          closePositionFn(pos.id);

          // Remove SLTP entry
          setSltpMap((prev) => {
            const next = { ...prev };
            delete next[pos.id];
            return next;
          });

          // Push notification
          const label = reason === "stop_loss" ? "Stop Loss" : "Take Profit";
          pushNotificationFn(
            "trade",
            `${pos.asset} ${label} Hit at $${currentPrice.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
            `${pos.direction} position auto-closed. ${label} triggered at $${currentPrice.toLocaleString()}`
          );
        }
      }

      if (events.length > 0) {
        setAutoCloseHistory((prev) => [...events, ...prev].slice(0, 50));
      }

      return events;
    },
    [positions, closePositionFn, pushNotificationFn]
  );

  // Clean up SLTP entries for positions that no longer exist
  useEffect(() => {
    const posIds = new Set(positions.map((p) => p.id));
    setSltpMap((prev) => {
      const next: Record<string, PositionSLTP> = {};
      let changed = false;
      for (const [id, sltp] of Object.entries(prev)) {
        if (posIds.has(id)) {
          next[id] = sltp;
        } else {
          changed = true;
        }
      }
      return changed ? next : prev;
    });
  }, [positions]);

  return {
    sltpMap,
    autoCloseHistory,
    setSLTP,
    removeSLTP,
    getSLTP,
    checkSLTP,
  };
}
