// =============================================================================
// src/components/ui/hud-panel.tsx — HUD-style panel with corner brackets
// =============================================================================

import { cn } from "@/lib/utils";

interface HudPanelProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
  scanLine?: boolean;
}

export function HudPanel({ title, children, className, scanLine }: HudPanelProps) {
  return (
    <div className={cn("hud-panel hud-corners overflow-hidden", className)}>
      {title && (
        <div className="flex items-center gap-2 border-b border-hud-border px-3 py-1.5">
          <div className="h-1.5 w-1.5 rounded-full bg-hud-cyan animate-pulse-live" />
          <span className="hud-label">{title}</span>
        </div>
      )}
      <div className="relative">
        {scanLine && <div className="hud-scan-line" />}
        {children}
      </div>
    </div>
  );
}
