// =============================================================================
// src/hooks/use-chart-drawings.ts — Chart Drawing State Management
//
// Manages drawing tools (trendline, horizontal, fibonacci, rectangle) with
// localStorage persistence per symbol.
// =============================================================================

"use client";

import { useCallback, useEffect, useState } from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type DrawingTool =
  | "none"
  | "trendline"
  | "horizontal"
  | "fibonacci"
  | "rectangle";

export interface DrawingPoint {
  price: number;
  time: number; // Unix timestamp in seconds
}

export interface ChartDrawing {
  id: string;
  type: DrawingTool;
  points: DrawingPoint[];
  color: string;
  style: "solid" | "dashed";
}

// Default colors per drawing type
export const DRAWING_COLORS: Record<Exclude<DrawingTool, "none">, string> = {
  trendline: "#3b82f6",
  horizontal: "#f59e0b",
  fibonacci: "#8b5cf6",
  rectangle: "#10b981",
};

// ---------------------------------------------------------------------------
// localStorage helpers
// ---------------------------------------------------------------------------

const STORAGE_KEY = "jarvis-chart-drawings";

function loadDrawings(symbol: string): ChartDrawing[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const all: Record<string, ChartDrawing[]> = JSON.parse(raw);
    return all[symbol] ?? [];
  } catch {
    return [];
  }
}

function saveDrawings(symbol: string, drawings: ChartDrawing[]) {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const all: Record<string, ChartDrawing[]> = raw ? JSON.parse(raw) : {};
    all[symbol] = drawings;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(all));
  } catch {
    // silently fail
  }
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useChartDrawings(symbol: string) {
  const [drawings, setDrawings] = useState<ChartDrawing[]>([]);
  const [activeTool, setActiveTool] = useState<DrawingTool>("none");

  // Load from localStorage when symbol changes
  useEffect(() => {
    setDrawings(loadDrawings(symbol));
  }, [symbol]);

  // Persist whenever drawings change
  useEffect(() => {
    saveDrawings(symbol, drawings);
  }, [symbol, drawings]);

  const addDrawing = useCallback((drawing: ChartDrawing) => {
    setDrawings((prev) => [...prev, drawing]);
  }, []);

  const removeDrawing = useCallback((id: string) => {
    setDrawings((prev) => prev.filter((d) => d.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setDrawings([]);
  }, []);

  const undoLast = useCallback(() => {
    setDrawings((prev) => prev.slice(0, -1));
  }, []);

  return {
    drawings,
    activeTool,
    setActiveTool,
    addDrawing,
    removeDrawing,
    clearAll,
    undoLast,
  };
}
