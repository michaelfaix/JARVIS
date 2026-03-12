// =============================================================================
// src/components/ui/api-offline-banner.tsx — Reusable backend-offline banner
// =============================================================================

"use client";

import { WifiOff } from "lucide-react";

interface ApiOfflineBannerProps {
  message?: string;
}

export function ApiOfflineBanner({
  message = "JARVIS Backend offline — showing cached data",
}: ApiOfflineBannerProps) {
  return (
    <div className="flex items-center gap-2 rounded-lg bg-yellow-500/10 border border-yellow-500/20 px-4 py-2.5 text-sm text-yellow-400">
      <WifiOff className="h-4 w-4 shrink-0" />
      <span>{message}</span>
    </div>
  );
}
