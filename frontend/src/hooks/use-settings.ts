"use client";

import { useCallback, useEffect, useState } from "react";
import type { AppSettings } from "@/lib/types";
import { loadJSON, saveJSON } from "@/lib/storage";
import { DEFAULT_CAPITAL, DEFAULT_ASSETS } from "@/lib/constants";
import { createClient } from "@/lib/supabase/client";
import { useAuth } from "@/hooks/use-auth";

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
  const { user } = useAuth();
  const supabase = createClient();

  // Load: Supabase first, then localStorage
  useEffect(() => {
    if (!user) {
      setSettings(loadJSON(KEY, DEFAULTS));
      return;
    }

    (async () => {
      const { data } = await supabase
        .from("user_settings")
        .select("settings")
        .eq("user_id", user.id)
        .single();

      if (data?.settings && Object.keys(data.settings as object).length > 0) {
        const merged = { ...DEFAULTS, ...(data.settings as Partial<AppSettings>) };
        setSettings(merged);
        saveJSON(KEY, merged);
      } else {
        // Migrate localStorage to Supabase
        const local = loadJSON(KEY, DEFAULTS);
        setSettings(local);
        supabase
          .from("user_settings")
          .upsert({
            user_id: user.id,
            settings: local,
            updated_at: new Date().toISOString(),
          })
          .then(() => {});
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id]);

  const update = useCallback(
    (patch: Partial<AppSettings>) => {
      setSettings((prev) => {
        const next = { ...prev, ...patch };
        saveJSON(KEY, next);
        if (user) {
          supabase
            .from("user_settings")
            .upsert({
              user_id: user.id,
              settings: next,
              updated_at: new Date().toISOString(),
            })
            .then(() => {});
        }
        return next;
      });
    },
    [user, supabase]
  );

  const reset = useCallback(() => {
    setSettings(DEFAULTS);
    saveJSON(KEY, DEFAULTS);
    if (user) {
      supabase
        .from("user_settings")
        .upsert({
          user_id: user.id,
          settings: DEFAULTS,
          updated_at: new Date().toISOString(),
        })
        .then(() => {});
    }
  }, [user, supabase]);

  return { settings, update, reset };
}
