// =============================================================================
// src/components/layout/app-header.tsx — Top header bar
// =============================================================================

"use client";

import { Badge } from "@/components/ui/badge";

interface AppHeaderProps {
  title: string;
  subtitle?: string;
}

export function AppHeader({ title, subtitle }: AppHeaderProps) {
  return (
    <header className="flex h-14 items-center justify-between border-b border-border/50 px-6">
      <div className="flex items-center gap-3">
        <h1 className="text-lg font-bold text-white">{title}</h1>
        {subtitle && (
          <span className="text-sm text-muted-foreground">{subtitle}</span>
        )}
      </div>
      <div className="flex items-center gap-3">
        <Badge variant="outline" className="text-[10px] text-muted-foreground">
          Paper Trading
        </Badge>
        <Badge variant="outline" className="text-[10px] text-green-400 border-green-400/30">
          RESEARCH ONLY
        </Badge>
      </div>
    </header>
  );
}
