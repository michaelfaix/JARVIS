// =============================================================================
// src/hooks/use-social-trading.ts — Social trading state management
// =============================================================================

"use client";

import { useCallback, useEffect, useState } from "react";
import { loadJSON, saveJSON } from "@/lib/storage";
import { useProfile } from "@/hooks/use-profile";

const STORAGE_KEY = "jarvis-social";
const MAX_FREE_FOLLOWS = 10;

export interface CopySettings {
  enabled: boolean;
  maxCapitalPercent: number;
  autoFollow: boolean;
}

interface SocialTradingState {
  followedTraders: string[];
  copySettings: Record<string, CopySettings>;
}

function defaultState(): SocialTradingState {
  return {
    followedTraders: [],
    copySettings: {},
  };
}

export function useSocialTrading() {
  const [state, setState] = useState<SocialTradingState>(defaultState);
  const { isPro } = useProfile();

  // Load from localStorage on mount
  useEffect(() => {
    const loaded = loadJSON<SocialTradingState>(STORAGE_KEY, defaultState());
    if (!loaded.followedTraders) loaded.followedTraders = [];
    if (!loaded.copySettings) loaded.copySettings = {};
    setState(loaded);
  }, []);

  const persist = useCallback((next: SocialTradingState) => {
    saveJSON(STORAGE_KEY, next);
  }, []);

  const followTrader = useCallback(
    (traderId: string) => {
      setState((prev) => {
        if (prev.followedTraders.includes(traderId)) return prev;
        if (!isPro && prev.followedTraders.length >= MAX_FREE_FOLLOWS) return prev;
        const next: SocialTradingState = {
          ...prev,
          followedTraders: [...prev.followedTraders, traderId],
          copySettings: {
            ...prev.copySettings,
            [traderId]: prev.copySettings[traderId] ?? {
              enabled: false,
              maxCapitalPercent: 5,
              autoFollow: false,
            },
          },
        };
        persist(next);
        return next;
      });
    },
    [isPro, persist]
  );

  const unfollowTrader = useCallback(
    (traderId: string) => {
      setState((prev) => {
        const next: SocialTradingState = {
          ...prev,
          followedTraders: prev.followedTraders.filter((id) => id !== traderId),
        };
        // Keep copy settings in case they re-follow
        persist(next);
        return next;
      });
    },
    [persist]
  );

  const isFollowing = useCallback(
    (traderId: string): boolean => {
      return state.followedTraders.includes(traderId);
    },
    [state.followedTraders]
  );

  const setCopySettings = useCallback(
    (traderId: string, settings: Partial<CopySettings>) => {
      setState((prev) => {
        const current = prev.copySettings[traderId] ?? {
          enabled: false,
          maxCapitalPercent: 5,
          autoFollow: false,
        };
        const next: SocialTradingState = {
          ...prev,
          copySettings: {
            ...prev.copySettings,
            [traderId]: { ...current, ...settings },
          },
        };
        persist(next);
        return next;
      });
    },
    [persist]
  );

  const maxFollows = isPro ? Infinity : MAX_FREE_FOLLOWS;
  const followCount = state.followedTraders.length;
  const canFollow = isPro || followCount < MAX_FREE_FOLLOWS;

  return {
    followedTraders: state.followedTraders,
    copySettings: state.copySettings,
    followTrader,
    unfollowTrader,
    isFollowing,
    setCopySettings,
    maxFollows,
    followCount,
    canFollow,
  };
}
