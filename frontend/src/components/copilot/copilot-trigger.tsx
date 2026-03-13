// =============================================================================
// src/components/copilot/copilot-trigger.tsx — Floating JARVIS trigger button
// =============================================================================

"use client";

import { Bot } from "lucide-react";

interface CoPilotTriggerProps {
  onClick: () => void;
  pulse?: boolean;
}

export function CoPilotTrigger({ onClick, pulse = false }: CoPilotTriggerProps) {
  return (
    <button
      onClick={onClick}
      className="fixed bottom-20 right-4 md:bottom-6 md:right-6 z-30
        flex h-12 w-12 items-center justify-center rounded-full
        bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-600/30
        transition-all hover:scale-105 active:scale-95"
      title="JARVIS Co-Pilot"
    >
      <Bot className="h-5 w-5" />
      {pulse && (
        <span className="absolute top-0 right-0 w-3 h-3 rounded-full bg-yellow-400 animate-ping" />
      )}
    </button>
  );
}
