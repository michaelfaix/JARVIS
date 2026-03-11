"use client";

import { useCallback, useEffect, useState } from "react";
import type { AppSettings } from "@/lib/types";
import { loadJSON, saveJSON } from "@/lib/storage";
import { DEFAULT_CAPITAL, DEFAULT_ASSETS } from "@/lib/constants";

const KEY = "jarvis-settings";

const DEFAULTS: AppSettings = {
  paperCapital: DEFAULT_CAPITAL,
  strategy: "momentum",
  theme: "dark",
  pollIntervalMs: 10000,
  trackedAssets: DEFAULT_ASSETS.map((a) => a.symbol),
};

export function useSettings() {
  const [settings, setSettings] = useState<AppSettings>(DEFAULTS);

  useEffect(() => {
    setSettings(loadJSON(KEY, DEFAULTS));
  }, []);

  const update = useCallback(
    (patch: Partial<AppSettings>) => {
      setSettings((prev) => {
        const next = { ...prev, ...patch };
        saveJSON(KEY, next);
        return next;
      });
    },
    []
  );

  const reset = useCallback(() => {
    setSettings(DEFAULTS);
    saveJSON(KEY, DEFAULTS);
  }, []);

  return { settings, update, reset };
}
