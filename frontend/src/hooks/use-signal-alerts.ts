// =============================================================================
// src/hooks/use-signal-alerts.ts — Auto-notify on high-confidence signals
// =============================================================================

"use client";

import { useCallback, useRef } from "react";
import type { Signal } from "@/lib/types";

const CONFIDENCE_THRESHOLD = 0.7;
const COOLDOWN_MS = 60_000; // Don't re-alert same asset within 1 minute

export function useSignalAlerts() {
  const lastAlerted = useRef<Record<string, number>>({});

  const checkSignals = useCallback((signals: Signal[]) => {
    if (typeof Notification === "undefined" || Notification.permission !== "granted") return;

    const now = Date.now();
    for (const signal of signals) {
      if (signal.confidence < CONFIDENCE_THRESHOLD) continue;

      const lastTime = lastAlerted.current[signal.asset] ?? 0;
      if (now - lastTime < COOLDOWN_MS) continue;

      lastAlerted.current[signal.asset] = now;

      new Notification(`JARVIS Signal: ${signal.asset} ${signal.direction}`, {
        body: `Confidence: ${(signal.confidence * 100).toFixed(0)}% | Entry: $${signal.entry.toLocaleString()} | Quality: ${(signal.qualityScore * 100).toFixed(0)}`,
        icon: "/icon-192.png",
        tag: `signal-${signal.asset}-${signal.direction}`,
      });
    }
  }, []);

  return { checkSignals };
}
