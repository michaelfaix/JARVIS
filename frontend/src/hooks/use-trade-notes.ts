// =============================================================================
// src/hooks/use-trade-notes.ts — Per-trade notes, tags & self-assessment
// =============================================================================

"use client";

import { useCallback, useState, useEffect } from "react";
import { loadJSON, saveJSON } from "@/lib/storage";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface TradeNote {
  tradeId: string;
  note: string; // free text
  tags: string[]; // e.g. ["momentum", "breakout", "news-driven"]
  rating: number; // 1-5 stars (self-assessment)
  updatedAt: string; // ISO timestamp
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

export const TAG_SUGGESTIONS = [
  "momentum",
  "breakout",
  "reversal",
  "news-driven",
  "technical",
  "fundamental",
  "scalp",
  "swing",
  "emotional",
  "planned",
] as const;

const STORAGE_KEY = "jarvis-trade-notes";

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useTradeNotes() {
  const [notes, setNotes] = useState<Record<string, TradeNote>>({});

  // Load from localStorage on mount
  useEffect(() => {
    setNotes(loadJSON<Record<string, TradeNote>>(STORAGE_KEY, {}));
  }, []);

  // Persist helper
  const persist = useCallback((next: Record<string, TradeNote>) => {
    setNotes(next);
    saveJSON(STORAGE_KEY, next);
  }, []);

  const getNote = useCallback(
    (tradeId: string): TradeNote | undefined => notes[tradeId],
    [notes]
  );

  const saveNote = useCallback(
    (tradeId: string, note: string, tags: string[], rating: number) => {
      const entry: TradeNote = {
        tradeId,
        note,
        tags,
        rating: Math.max(1, Math.min(5, rating)),
        updatedAt: new Date().toISOString(),
      };
      persist({ ...notes, [tradeId]: entry });
    },
    [notes, persist]
  );

  const deleteNote = useCallback(
    (tradeId: string) => {
      const next = { ...notes };
      delete next[tradeId];
      persist(next);
    },
    [notes, persist]
  );

  const getAllNotes = useCallback(
    (): TradeNote[] => Object.values(notes),
    [notes]
  );

  return { notes, getNote, saveNote, deleteNote, getAllNotes };
}
