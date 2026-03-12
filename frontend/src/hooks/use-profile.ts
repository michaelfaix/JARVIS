"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { useAuth } from "@/hooks/use-auth";

export type Tier = "free" | "pro" | "enterprise";

export interface Profile {
  id: string;
  displayName: string;
  tier: Tier;
}

export function useProfile() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const supabase = createClient();

  useEffect(() => {
    if (!user) {
      setProfile(null);
      setLoading(false);
      return;
    }

    supabase
      .from("profiles")
      .select("id, display_name, tier")
      .eq("id", user.id)
      .single()
      .then(({ data }) => {
        if (data) {
          setProfile({
            id: data.id,
            displayName: data.display_name ?? user.email?.split("@")[0] ?? "User",
            tier: (data.tier as Tier) ?? "free",
          });
        } else {
          setProfile({
            id: user.id,
            displayName: user.email?.split("@")[0] ?? "User",
            tier: "free",
          });
        }
        setLoading(false);
      });
  }, [user, supabase]);

  const isPro = profile?.tier === "pro" || profile?.tier === "enterprise";
  const isEnterprise = profile?.tier === "enterprise";

  return { profile, loading, isPro, isEnterprise, tier: profile?.tier ?? "free" };
}
