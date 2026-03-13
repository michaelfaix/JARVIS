// =============================================================================
// src/hooks/use-proactive-warnings.ts — Proactive JARVIS Notifications
//
// Watches system state and fires toast notifications on:
// - Regime changes, High OOD, Position near SL/TP, Strong signals
// =============================================================================

"use client";

import { useEffect, useRef } from "react";
import type { RegimeState } from "@/lib/types";

interface ProactiveWarningsInput {
  regime: RegimeState;
  oodScore: number;
  positions: { asset: string; direction: string; entryPrice: number }[];
  prices: Record<string, number>;
  slPercent: number;
  tpPercent: number;
  topSignalConfidence: number;
  topSignalAsset: string | null;
  topSignalDirection: string | null;
  push: (type: "signal" | "alert" | "system", title: string, message: string) => void;
}

const COOLDOWN_MS = 60_000; // 60s between same warning type

export function useProactiveWarnings({
  regime,
  oodScore,
  positions,
  prices,
  slPercent,
  tpPercent,
  topSignalConfidence,
  topSignalAsset,
  topSignalDirection,
  push,
}: ProactiveWarningsInput) {
  const prevRegimeRef = useRef<RegimeState>(regime);
  const lastWarningRef = useRef<Record<string, number>>({});

  const canFire = (key: string) => {
    const now = Date.now();
    const last = lastWarningRef.current[key] ?? 0;
    if (now - last < COOLDOWN_MS) return false;
    lastWarningRef.current[key] = now;
    return true;
  };

  // Regime change
  useEffect(() => {
    const prev = prevRegimeRef.current;
    prevRegimeRef.current = regime;
    if (prev === regime) return;
    if (!canFire("regime")) return;

    push(
      "system",
      "Regime Change",
      `Market shifted from ${prev.replace("_", " ")} to ${regime.replace("_", " ")}`,
    );
  }, [regime, push]);

  // High OOD
  useEffect(() => {
    if (oodScore <= 0.7) return;
    if (!canFire("ood")) return;

    push(
      "system",
      "High OOD Warning",
      `Out-of-Distribution score at ${(oodScore * 100).toFixed(0)}% — unusual market conditions detected`,
    );
  }, [oodScore, push]);

  // Position near SL/TP
  useEffect(() => {
    for (const pos of positions) {
      const price = prices[pos.asset];
      if (!price) continue;

      const isLong = pos.direction === "LONG";
      const slPrice = isLong
        ? pos.entryPrice * (1 - slPercent / 100)
        : pos.entryPrice * (1 + slPercent / 100);
      const tpPrice = isLong
        ? pos.entryPrice * (1 + tpPercent / 100)
        : pos.entryPrice * (1 - tpPercent / 100);

      const slDist = Math.abs(price - slPrice) / price;
      const tpDist = Math.abs(price - tpPrice) / price;

      if (slDist < 0.01 && canFire(`sl-${pos.asset}`)) {
        push("alert", `${pos.asset} Near Stop Loss`, `${pos.asset} is within 1% of your stop loss at $${slPrice.toFixed(2)}`);
      }
      if (tpDist < 0.01 && canFire(`tp-${pos.asset}`)) {
        push("alert", `${pos.asset} Near Take Profit`, `${pos.asset} is within 1% of your take profit at $${tpPrice.toFixed(2)}`);
      }
    }
  }, [positions, prices, slPercent, tpPercent, push]);

  // Strong signal
  useEffect(() => {
    if (topSignalConfidence <= 0.8) return;
    if (!topSignalAsset) return;
    if (!canFire("strong-signal")) return;

    push(
      "signal",
      `Strong ${topSignalDirection} Signal`,
      `${topSignalAsset} ${topSignalDirection} with ${(topSignalConfidence * 100).toFixed(0)}% confidence`,
    );
  }, [topSignalConfidence, topSignalAsset, topSignalDirection, push]);
}
