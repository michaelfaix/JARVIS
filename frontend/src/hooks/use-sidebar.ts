"use client";

import { useCallback, useEffect, useState } from "react";
import { loadJSON, saveJSON } from "@/lib/storage";

const KEY = "jarvis-sidebar-expanded";

export function useSidebar() {
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    setExpanded(loadJSON(KEY, false));
  }, []);

  const toggle = useCallback(() => {
    setExpanded((prev) => {
      const next = !prev;
      saveJSON(KEY, next);
      return next;
    });
  }, []);

  // Keep collapsed/toggle for backward compat with layout
  return { collapsed: !expanded, expanded, toggle };
}
