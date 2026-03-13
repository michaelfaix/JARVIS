// =============================================================================
// src/hooks/use-locale.ts — Locale management with React Context
// =============================================================================

"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import { type Locale, type TranslationKey, t as translate } from "@/lib/i18n";
import React from "react";

const STORAGE_KEY = "jarvis-locale";

interface LocaleContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: TranslationKey, vars?: Record<string, string | number>) => string;
}

const LocaleContext = createContext<LocaleContextValue | null>(null);

function getInitialLocale(): Locale {
  if (typeof window === "undefined") return "en";
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "en" || stored === "de") return stored;
  } catch {
    // localStorage not available
  }
  // Auto-detect browser language
  // Default to German (primary market)
  return "de";
}

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("en");
  const [mounted, setMounted] = useState(false);

  // Hydrate from localStorage / browser on mount
  useEffect(() => {
    setLocaleState(getInitialLocale());
    setMounted(true);
  }, []);

  const setLocale = useCallback((l: Locale) => {
    setLocaleState(l);
    try {
      localStorage.setItem(STORAGE_KEY, l);
    } catch {
      // ignore
    }
  }, []);

  const t = useCallback(
    (key: TranslationKey, vars?: Record<string, string | number>) =>
      translate(key, locale, vars),
    [locale],
  );

  // Avoid hydration mismatch: render with 'en' on server, update on mount
  const value: LocaleContextValue = {
    locale: mounted ? locale : "en",
    setLocale,
    t: mounted
      ? t
      : (key: TranslationKey, vars?: Record<string, string | number>) =>
          translate(key, "en", vars),
  };

  return React.createElement(
    LocaleContext.Provider,
    { value },
    children,
  );
}

export function useLocale(): LocaleContextValue {
  const ctx = useContext(LocaleContext);
  if (!ctx) {
    throw new Error("useLocale must be used within a LocaleProvider");
  }
  return ctx;
}
