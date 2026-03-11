"use client";

import { useCallback, useEffect, useState } from "react";
import { loadJSON, saveJSON } from "@/lib/storage";

const KEY = "jarvis-sidebar-collapsed";

export function useSidebar() {
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    setCollapsed(loadJSON(KEY, false));
  }, []);

  const toggle = useCallback(() => {
    setCollapsed((prev) => {
      const next = !prev;
      saveJSON(KEY, next);
      return next;
    });
  }, []);

  return { collapsed, toggle };
}
