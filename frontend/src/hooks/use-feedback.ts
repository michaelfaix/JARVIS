// =============================================================================
// src/hooks/use-feedback.ts — Auto-send trade outcomes to JARVIS backend
//
// When a trade closes, sends feedback to /feedback so the ML model can learn.
// Maps trade P&L to the backend's feedback schema (GEFOLGT/ERFOLG/FEHLER).
// Tracks feedback history and accuracy stats locally.
// =============================================================================

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { postFeedback } from "@/lib/api";
import { loadJSON, saveJSON } from "@/lib/storage";
import type { ClosedTrade } from "@/lib/types";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface FeedbackRecord {
  tradeId: string;
  asset: string;
  direction: "LONG" | "SHORT";
  pnl: number;
  pnlPercent: number;
  sentAt: string;
  accepted: boolean;
  labelWert: number | null;
}

interface SignalAccuracy {
  asset: string;
  totalTrades: number;
  wins: number;
  losses: number;
  winRate: number;
  avgPnlPercent: number;
}

// ---------------------------------------------------------------------------
// Storage
// ---------------------------------------------------------------------------

const FEEDBACK_KEY = "jarvis-feedback-history";
const SENT_IDS_KEY = "jarvis-feedback-sent";

function loadFeedbackHistory(): FeedbackRecord[] {
  return loadJSON<FeedbackRecord[]>(FEEDBACK_KEY, []);
}

function loadSentIds(): Set<string> {
  return new Set(loadJSON<string[]>(SENT_IDS_KEY, []));
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useFeedback(closedTrades: ClosedTrade[]) {
  const [feedbackHistory, setFeedbackHistory] = useState<FeedbackRecord[]>(
    loadFeedbackHistory
  );
  const [sending, setSending] = useState(false);
  const sentIdsRef = useRef<Set<string>>(loadSentIds());

  // Persist feedback history
  useEffect(() => {
    saveJSON(FEEDBACK_KEY, feedbackHistory.slice(0, 200));
  }, [feedbackHistory]);

  // Send feedback for a single trade
  const sendFeedback = useCallback(async (trade: ClosedTrade) => {
    // Determine outcome
    const isWin = trade.pnl > 0;
    const isNeutral = Math.abs(trade.pnlPercent) < 0.5; // < 0.5% = neutral
    const ergebnis = isNeutral ? "NEUTRAL" : isWin ? "ERFOLG" : "FEHLER";

    // Prediction error: absolute P&L percent as a proxy
    const predError = Math.abs(trade.pnlPercent) / 100;

    try {
      const res = await postFeedback({
        prediction_id: trade.id,
        benutzer_aktion: "GEFOLGT", // User followed the signal by opening a trade
        ergebnis: ergebnis as "ERFOLG" | "NEUTRAL" | "FEHLER",
        konfidenz: Math.min(1, Math.max(0, 0.5 + Math.abs(trade.pnlPercent) / 200)),
        tatsaechliches_ergebnis: trade.pnlPercent / 100,
        vorhersage_fehler: predError,
      });

      const record: FeedbackRecord = {
        tradeId: trade.id,
        asset: trade.asset,
        direction: trade.direction,
        pnl: trade.pnl,
        pnlPercent: trade.pnlPercent,
        sentAt: new Date().toISOString(),
        accepted: res.accepted,
        labelWert: res.label_wert,
      };

      setFeedbackHistory((prev) => [record, ...prev].slice(0, 200));
      sentIdsRef.current.add(trade.id);
      saveJSON(SENT_IDS_KEY, Array.from(sentIdsRef.current));

      return true;
    } catch {
      // Backend offline — will retry next time
      return false;
    }
  }, []);

  // Auto-send feedback for new closed trades
  useEffect(() => {
    if (closedTrades.length === 0) return;

    const unsent = closedTrades.filter(
      (t) => !sentIdsRef.current.has(t.id)
    );
    if (unsent.length === 0) return;

    setSending(true);
    Promise.allSettled(unsent.map(sendFeedback)).finally(() => {
      setSending(false);
    });
  }, [closedTrades, sendFeedback]);

  // Compute per-asset accuracy stats
  const accuracyByAsset: SignalAccuracy[] = (() => {
    const map = new Map<string, { wins: number; losses: number; totalPnlPct: number }>();
    for (const record of feedbackHistory) {
      const existing = map.get(record.asset) ?? { wins: 0, losses: 0, totalPnlPct: 0 };
      if (record.pnl > 0) existing.wins++;
      else existing.losses++;
      existing.totalPnlPct += record.pnlPercent;
      map.set(record.asset, existing);
    }
    return Array.from(map.entries()).map(([asset, stats]) => ({
      asset,
      totalTrades: stats.wins + stats.losses,
      wins: stats.wins,
      losses: stats.losses,
      winRate: stats.wins / (stats.wins + stats.losses) * 100,
      avgPnlPercent: stats.totalPnlPct / (stats.wins + stats.losses),
    }));
  })();

  return {
    feedbackHistory,
    accuracyByAsset,
    sending,
    sendFeedback,
  };
}
