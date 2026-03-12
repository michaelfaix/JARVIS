// =============================================================================
// src/hooks/use-subscription.ts — Subscription management hook
// =============================================================================

"use client";

import { useState } from "react";
import { useToast } from "@/components/ui/toast";

export function useSubscription() {
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const subscribe = async (tier: "pro" | "enterprise") => {
    setLoading(true);
    try {
      const res = await fetch("/api/stripe/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tier }),
      });

      const data = await res.json();

      if (!res.ok) {
        toast("error", data.error ?? "Failed to create checkout session");
        return;
      }

      if (data.url) {
        window.location.href = data.url;
      }
    } catch {
      toast("error", "Failed to start checkout. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const manageSubscription = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/stripe/portal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      const data = await res.json();

      if (!res.ok) {
        toast("error", data.error ?? "Failed to open billing portal");
        return;
      }

      if (data.url) {
        window.location.href = data.url;
      }
    } catch {
      toast("error", "Failed to open billing portal. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return { subscribe, manageSubscription, loading };
}
