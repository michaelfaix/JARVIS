// =============================================================================
// src/hooks/use-copilot.ts — JARVIS Co-Pilot Hook
//
// Manages chat state, risk profile, locale, pattern recognition,
// offline response generation, and alert creation from chat.
// =============================================================================

"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { loadJSON, saveJSON } from "@/lib/storage";
import {
  generateOfflineResponse,
  parseAlertFromMessage,
  calculateConfidence,
  calculateRiskReward,
  type RiskProfile,
  type Locale,
  type CoPilotContext,
  type PatternInfo,
} from "@/lib/copilot-engine";
import { detectAllPatterns, type PatternResult } from "@/lib/pattern-recognition";
import type { RegimeState } from "@/lib/types";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface CoPilotMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

export interface CoPilotState {
  mounted: boolean;
  messages: CoPilotMessage[];
  isTyping: boolean;
  riskProfile: RiskProfile;
  locale: Locale;
  confidence: number;
  riskReward: { ratio: number; rating: "good" | "neutral" | "bad" };
  patterns: PatternResult[];
  supportLevels: number[];
  resistanceLevels: number[];
}

export interface CoPilotInput {
  regime: RegimeState;
  ece: number;
  oodScore: number;
  metaUncertainty: number;
  strategy: string;
  selectedAsset: string;
  interval: string;
  slPercent: number;
  tpPercent: number;
  currentPrice: number;
  totalValue: number;
  drawdown: number;
  positionCount: number;
  closedTradeCount: number;
  realizedPnl: number;
  winRate: number;
  signalCount: number;
  topSignalAsset: string | null;
  topSignalDirection: string | null;
  topSignalConfidence: number;
  candles: { time: number; open: number; high: number; low: number; close: number }[];
  addAlert?: (alert: { asset: string; condition: "above" | "below"; targetPrice: number }) => void;
}

const MAX_MESSAGES = 50;
const HISTORY_KEY = "jarvis-copilot-history";
const PROFILE_KEY = "jarvis-copilot-profile";
const LOCALE_KEY = "jarvis-copilot-locale";

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useCoPilot(input: CoPilotInput) {
  const [mounted, setMounted] = useState(false);
  const [messages, setMessages] = useState<CoPilotMessage[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [riskProfile, setRiskProfileState] = useState<RiskProfile>("moderate");
  const [locale, setLocaleState] = useState<Locale>("de");

  const typingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Hydrate from localStorage after mount to avoid SSR mismatch
  useEffect(() => {
    setMessages(loadJSON<CoPilotMessage[]>(HISTORY_KEY, []));
    setRiskProfileState(loadJSON<RiskProfile>(PROFILE_KEY, "moderate"));
    setLocaleState(loadJSON<Locale>(LOCALE_KEY, "de"));
    setMounted(true);
  }, []);

  // --- Pattern recognition (memoized on candles) ---
  const candlesKey = input.candles.length > 0 ? `${input.candles[0]?.time}-${input.candles.length}` : "";
  const patterns = useMemo(() => {
    if (input.candles.length < 20) return [];
    return detectAllPatterns(input.candles);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [candlesKey]);

  const supportLevels = useMemo(
    () => patterns.filter((p) => p.type === "Support").map((p) => p.priceLevel!).filter(Boolean),
    [patterns]
  );
  const resistanceLevels = useMemo(
    () => patterns.filter((p) => p.type === "Resistance").map((p) => p.priceLevel!).filter(Boolean),
    [patterns]
  );

  // --- Computed values ---
  const confidence = useMemo(
    () => calculateConfidence(input.ece, input.oodScore, input.topSignalConfidence, input.regime),
    [input.ece, input.oodScore, input.topSignalConfidence, input.regime]
  );

  const riskReward = useMemo(
    () => calculateRiskReward(input.currentPrice, input.slPercent, input.tpPercent),
    [input.currentPrice, input.slPercent, input.tpPercent]
  );

  // --- Build context ---
  const buildContext = useCallback((): CoPilotContext => {
    const patternInfos: PatternInfo[] = patterns
      .filter((p) => p.type !== "Support" && p.type !== "Resistance")
      .slice(0, 3)
      .map((p) => ({ type: p.type, description: p.description, confidence: p.confidence }));

    return {
      regime: input.regime,
      ece: input.ece,
      oodScore: input.oodScore,
      metaUncertainty: input.metaUncertainty,
      strategy: input.strategy,
      selectedAsset: input.selectedAsset,
      interval: input.interval,
      slPercent: input.slPercent,
      tpPercent: input.tpPercent,
      currentPrice: input.currentPrice,
      totalValue: input.totalValue,
      drawdown: input.drawdown,
      positionCount: input.positionCount,
      closedTradeCount: input.closedTradeCount,
      realizedPnl: input.realizedPnl,
      winRate: input.winRate,
      signalCount: input.signalCount,
      topSignalAsset: input.topSignalAsset,
      topSignalDirection: input.topSignalDirection,
      topSignalConfidence: input.topSignalConfidence,
      patterns: patternInfos,
    };
  }, [input, patterns]);

  // --- Send message ---
  const sendMessage = useCallback(
    (text: string) => {
      if (!text.trim() || isTyping) return;

      const userMsg: CoPilotMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content: text.trim(),
        timestamp: Date.now(),
      };

      setMessages((prev) => {
        const next = [...prev, userMsg].slice(-MAX_MESSAGES);
        saveJSON(HISTORY_KEY, next);
        return next;
      });

      setIsTyping(true);

      // Check for alert intent
      const alertParsed = parseAlertFromMessage(text);
      if (alertParsed && input.addAlert) {
        input.addAlert(alertParsed);
      }

      // Simulate typing delay (300-800ms)
      const delay = 300 + Math.random() * 500;
      typingTimerRef.current = setTimeout(() => {
        const ctx = buildContext();
        const response = generateOfflineResponse(text, ctx, locale, riskProfile);

        const assistantMsg: CoPilotMessage = {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: response,
          timestamp: Date.now(),
        };

        setMessages((prev) => {
          const next = [...prev, assistantMsg].slice(-MAX_MESSAGES);
          saveJSON(HISTORY_KEY, next);
          return next;
        });
        setIsTyping(false);
      }, delay);
    },
    [isTyping, buildContext, locale, riskProfile, input]
  );

  // --- Settings ---
  const setRiskProfile = useCallback((profile: RiskProfile) => {
    setRiskProfileState(profile);
    saveJSON(PROFILE_KEY, profile);
  }, []);

  const setLocale = useCallback((l: Locale) => {
    setLocaleState(l);
    saveJSON(LOCALE_KEY, l);
  }, []);

  const clearHistory = useCallback(() => {
    setMessages([]);
    saveJSON(HISTORY_KEY, []);
    if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
    setIsTyping(false);
  }, []);

  const state: CoPilotState = {
    mounted,
    messages,
    isTyping,
    riskProfile,
    locale,
    confidence,
    riskReward,
    patterns,
    supportLevels,
    resistanceLevels,
  };

  return {
    state,
    sendMessage,
    setRiskProfile,
    setLocale,
    clearHistory,
  };
}
