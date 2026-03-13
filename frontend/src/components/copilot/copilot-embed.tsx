// =============================================================================
// src/components/copilot/copilot-embed.tsx — Compact CoPilot embed strip
//
// 2-column compact strip below chart. Does NOT replace copilot-panel.tsx.
// Uses existing useCoPilot hook data.
// =============================================================================

"use client";

import { useRef, useState } from "react";
import { ArrowRight, Zap, Shield, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";
import type { CoPilotState } from "@/hooks/use-copilot";

interface CoPilotEmbedProps {
  state: CoPilotState;
  sendMessage: (msg: string) => void;
  onExpand: () => void;
}

const QUICK_ACTIONS = [
  { label: "Chart Analysis", emoji: "📊" },
  { label: "Risk Check", emoji: "🛡️" },
  { label: "Daily Review", emoji: "📋" },
];

export function CoPilotEmbed({ state, sendMessage, onExpand }: CoPilotEmbedProps) {
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const lastMessages = state.messages.slice(-3);
  const lastAnalysis = state.messages
    .filter((m) => m.role === "assistant")
    .slice(-1)[0];

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed) return;
    sendMessage(trimmed);
    setInput("");
  };

  const tipCards = [
    {
      icon: <Zap className="h-3 w-3 text-hud-amber" />,
      text: state.confidence ? `Confidence: ${(state.confidence * 100).toFixed(0)}%` : "Awaiting data...",
      color: "border-hud-amber/20",
    },
    {
      icon: <Shield className="h-3 w-3 text-hud-cyan" />,
      text: `Risk: ${state.riskProfile}`,
      color: "border-hud-cyan/20",
    },
    {
      icon: <TrendingUp className="h-3 w-3 text-hud-green" />,
      text: state.riskReward ? `R:R ${state.riskReward.ratio.toFixed(1)}x` : "No R:R data",
      color: "border-hud-green/20",
    },
  ];

  return (
    <div className="rounded border border-hud-border bg-hud-panel/60 overflow-hidden">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-0">
        {/* Left: Avatar + analysis + tips */}
        <div className="p-3 border-b md:border-b-0 md:border-r border-hud-border/50 space-y-2">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded bg-hud-cyan/20 text-hud-cyan font-mono text-xs font-bold shrink-0">
              J
            </div>
            <div className="h-1.5 w-1.5 rounded-full bg-hud-green animate-pulse-live" />
            <span className="hud-label">JARVIS CO-PILOT</span>
            <button
              onClick={onExpand}
              className="ml-auto flex items-center gap-1 text-[9px] font-mono text-muted-foreground hover:text-hud-cyan transition-colors"
            >
              Expand <ArrowRight className="h-2.5 w-2.5" />
            </button>
          </div>

          {/* Last analysis text */}
          {lastAnalysis && (
            <p className="text-[10px] text-muted-foreground line-clamp-2 leading-relaxed">
              {lastAnalysis.content}
            </p>
          )}

          {/* Tip cards */}
          <div className="flex gap-1.5">
            {tipCards.map((tip, i) => (
              <div
                key={i}
                className={cn(
                  "flex items-center gap-1 px-1.5 py-1 rounded border bg-hud-bg/50 text-[9px] font-mono flex-1",
                  tip.color
                )}
              >
                {tip.icon}
                <span className="text-muted-foreground truncate">{tip.text}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Messages + input */}
        <div className="p-3 space-y-2">
          {/* Recent messages */}
          <div className="space-y-1 max-h-16 overflow-y-auto">
            {lastMessages.length === 0 ? (
              <p className="text-[10px] text-muted-foreground/50 italic">
                Ask JARVIS anything about your trades...
              </p>
            ) : (
              lastMessages.map((msg) => (
                <div
                  key={msg.id}
                  className={cn(
                    "text-[10px] truncate",
                    msg.role === "user"
                      ? "text-hud-cyan"
                      : "text-muted-foreground"
                  )}
                >
                  <span className="font-mono text-[8px] uppercase mr-1 opacity-50">
                    {msg.role === "user" ? "you" : "j"}:
                  </span>
                  {msg.content}
                </div>
              ))
            )}
          </div>

          {/* Input */}
          <div className="flex items-center gap-1.5">
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Frag JARVIS..."
              className="flex-1 bg-hud-bg/80 border border-hud-border rounded px-2 py-1 text-[10px] font-mono text-white placeholder:text-muted-foreground/40 focus:outline-none focus:border-hud-cyan/50"
            />
            <button
              onClick={handleSend}
              className="px-2 py-1 rounded border border-hud-cyan/30 bg-hud-cyan/10 text-[9px] font-mono text-hud-cyan hover:bg-hud-cyan/20 transition-colors"
            >
              Send
            </button>
          </div>

          {/* Quick actions */}
          <div className="flex gap-1">
            {QUICK_ACTIONS.map((action) => (
              <button
                key={action.label}
                onClick={() => sendMessage(action.label)}
                className="flex items-center gap-0.5 px-1.5 py-0.5 rounded border border-hud-border text-[8px] font-mono text-muted-foreground hover:text-hud-cyan hover:border-hud-cyan/30 transition-colors"
                suppressHydrationWarning
              >
                <span>{action.emoji}</span>
                <span className="hidden sm:inline" suppressHydrationWarning>{action.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
