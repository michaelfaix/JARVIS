import React from "react";
import { HudPanel } from "@/components/ui/hud-panel";

interface StatCardProps {
  label: string;
  value: string;
}

export const StatCard = React.memo(function StatCard({ label, value }: StatCardProps) {
  return (
    <HudPanel>
      <div className="px-3 py-2.5">
        <div className="text-[9px] font-mono text-muted-foreground/60 uppercase tracking-wider mb-0.5">{label}</div>
        <div className="text-lg font-bold font-mono text-white">{value}</div>
      </div>
    </HudPanel>
  );
});
