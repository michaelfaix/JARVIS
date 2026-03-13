// =============================================================================
// src/hooks/use-widget-layout.ts — Widget layout state with localStorage
// =============================================================================

"use client";

import { useCallback, useEffect, useState } from "react";
import { loadJSON, saveJSON } from "@/lib/storage";
import type { Layout, LayoutItem } from "react-grid-layout";

const STORAGE_KEY = "jarvis-widget-layout-v1";

export interface WidgetLayoutState {
  layouts: LayoutItem[];
  activeWidgets: string[];
}

const DEFAULT_LAYOUTS: LayoutItem[] = [
  { i: "system-status", x: 0, y: 0, w: 2, h: 4 },
  { i: "portfolio", x: 0, y: 4, w: 4, h: 3 },
  { i: "watchlist", x: 4, y: 4, w: 4, h: 3 },
  { i: "signals", x: 8, y: 0, w: 2, h: 4 },
  { i: "sentiment", x: 0, y: 7, w: 3, h: 3 },
  { i: "signal-quality", x: 8, y: 4, w: 2, h: 4 },
  { i: "activity", x: 3, y: 7, w: 3, h: 3 },
];

const DEFAULT_ACTIVE = DEFAULT_LAYOUTS.map((l) => l.i);

export function useWidgetLayout() {
  const [layouts, setLayouts] = useState<LayoutItem[]>(DEFAULT_LAYOUTS);
  const [activeWidgets, setActiveWidgets] = useState<string[]>(DEFAULT_ACTIVE);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const saved = loadJSON<WidgetLayoutState | null>(STORAGE_KEY, null);
    if (saved) {
      setLayouts(saved.layouts);
      setActiveWidgets(saved.activeWidgets);
    }
    setMounted(true);
  }, []);

  const persist = useCallback((l: LayoutItem[], a: string[]) => {
    saveJSON(STORAGE_KEY, { layouts: l, activeWidgets: a });
  }, []);

  const onLayoutChange = useCallback(
    (newLayout: Layout) => {
      const mutable = [...newLayout];
      setLayouts(mutable);
      persist(mutable, activeWidgets);
    },
    [activeWidgets, persist]
  );

  const addWidget = useCallback(
    (id: string) => {
      if (activeWidgets.includes(id)) return;
      const next = [...activeWidgets, id];
      const defaultL = DEFAULT_LAYOUTS.find((l) => l.i === id);
      const newLayout = [
        ...layouts,
        defaultL ?? { i: id, x: 0, y: Infinity, w: 3, h: 3 },
      ];
      setActiveWidgets(next);
      setLayouts(newLayout);
      persist(newLayout, next);
    },
    [activeWidgets, layouts, persist]
  );

  const removeWidget = useCallback(
    (id: string) => {
      const next = activeWidgets.filter((w) => w !== id);
      const newLayout = layouts.filter((l) => l.i !== id);
      setActiveWidgets(next);
      setLayouts(newLayout);
      persist(newLayout, next);
    },
    [activeWidgets, layouts, persist]
  );

  const resetLayout = useCallback(() => {
    setLayouts(DEFAULT_LAYOUTS);
    setActiveWidgets(DEFAULT_ACTIVE);
    persist(DEFAULT_LAYOUTS, DEFAULT_ACTIVE);
  }, [persist]);

  return {
    layouts,
    activeWidgets,
    mounted,
    onLayoutChange,
    addWidget,
    removeWidget,
    resetLayout,
  };
}
