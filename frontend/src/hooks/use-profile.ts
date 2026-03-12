"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { useAuth } from "@/hooks/use-auth";

export type Tier = "free" | "pro" | "enterprise";

// Owner/admin emails that always get enterprise tier
const ADMIN_EMAILS = ["mfaix90@gmail.com"];

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

    const isAdmin = ADMIN_EMAILS.includes(user.email ?? "");

    supabase
      .from("profiles")
      .select("id, display_name, tier")
      .eq("id", user.id)
      .single()
      .then(({ data }) => {
        const baseTier = (data?.tier as Tier) ?? "free";
        setProfile({
          id: data?.id ?? user.id,
          displayName: data?.display_name ?? user.email?.split("@")[0] ?? "User",
          tier: isAdmin ? "enterprise" : baseTier,
        });
        setLoading(false);
      });
  }, [user, supabase]);

  const isPro = profile?.tier === "pro" || profile?.tier === "enterprise";
  const isEnterprise = profile?.tier === "enterprise";

  return { profile, loading, isPro, isEnterprise, tier: profile?.tier ?? "free" };
}
