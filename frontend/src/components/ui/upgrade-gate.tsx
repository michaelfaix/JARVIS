"use client";

import { Lock, Sparkles } from "lucide-react";
import type { Tier } from "@/hooks/use-profile";

interface UpgradeGateProps {
  currentTier: Tier;
  requiredTier: "pro" | "enterprise";
  feature: string;
  children: React.ReactNode;
}

const TIER_LABELS: Record<string, string> = {
  pro: "Pro",
  enterprise: "Enterprise",
};

export function UpgradeGate({
  currentTier,
  requiredTier,
  feature,
  children,
}: UpgradeGateProps) {
  const tierRank = { free: 0, pro: 1, enterprise: 2 };

  if (tierRank[currentTier] >= tierRank[requiredTier]) {
    return <>{children}</>;
  }

  return (
    <div className="flex flex-col items-center justify-center py-24 px-6 text-center">
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-600/20">
        <Lock className="h-8 w-8 text-blue-400" />
      </div>
      <h2 className="text-2xl font-bold text-white">{feature}</h2>
      <p className="mt-2 max-w-md text-sm text-muted-foreground">
        This feature requires a {TIER_LABELS[requiredTier]} subscription.
        Upgrade to unlock {feature.toLowerCase()} and more.
      </p>
      <a
        href="/landing#pricing"
        className="mt-6 flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blue-600/25 hover:bg-blue-700 transition-colors"
      >
        <Sparkles className="h-4 w-4" />
        Upgrade to {TIER_LABELS[requiredTier]}
      </a>
    </div>
  );
}
