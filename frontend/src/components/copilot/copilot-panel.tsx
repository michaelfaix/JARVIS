// =============================================================================
// src/components/copilot/copilot-panel.tsx — JARVIS Co-Pilot Slide-In Panel
//
// Full-featured AI co-pilot: chat, quick actions, confidence, R:R, patterns,
// risk profile, locale toggle, typing indicator, glassmorphism overlay.
// =============================================================================

"use client";

import { useCallback, useEffect, useRef } from "react";
import { simpleMarkdown } from "@/lib/markdown";
import type { CoPilotState } from "@/hooks/use-copilot";
import type { RiskProfile, Locale } from "@/lib/copilot-engine";
import {
  Bot,
  User,
  Send,
  X,
  Trash2,
  Shield,
  Zap,
  Target,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Quick Actions (Feature 11)
// ---------------------------------------------------------------------------

interface QuickAction {
  icon: string;
  label: Record<Locale, string>;
  prompt: Record<Locale, string>;
}

const QUICK_ACTIONS: QuickAction[] = [
  {
    icon: "📊",
    label: { de: "Chart analysieren", en: "Analyze Chart" },
    prompt: { de: "Analysiere den aktuellen Chart", en: "Analyze the current chart" },
  },
  {
    icon: "🎯",
    label: { de: "Beste Strategie?", en: "Best Strategy?" },
    prompt: { de: "Welche Strategie empfiehlst du?", en: "What strategy do you recommend?" },
  },
  {
    icon: "📈",
    label: { de: "R:R berechnen", en: "Calculate R:R" },
    prompt: { de: "Berechne das Risk/Reward", en: "Calculate the risk/reward" },
  },
  {
    icon: "🔔",
    label: { de: "Alert setzen", en: "Set Alert" },
    prompt: { de: "Sag mir wenn BTC $75000 erreicht", en: "Tell me when BTC hits $75000" },
  },
  {
    icon: "📋",
    label: { de: "Tagesrueckblick", en: "Daily Review" },
    prompt: { de: "Zeige mir den Tagesrueckblick", en: "Show me the daily review" },
  },
  {
    icon: "⚙️",
    label: { de: "Custom Strategie", en: "Custom Strategy" },
    prompt: { de: "Wie erstelle ich eine eigene Strategie?", en: "How do I create a custom strategy?" },
  },
];

const RISK_PROFILES: { id: RiskProfile; icon: typeof Shield; label: Record<Locale, string>; color: string }[] = [
  { id: "conservative", icon: Shield, label: { de: "Konservativ", en: "Conservative" }, color: "text-blue-400" },
  { id: "moderate", icon: Target, label: { de: "Moderat", en: "Moderate" }, color: "text-yellow-400" },
  { id: "aggressive", icon: Zap, label: { de: "Aggressiv", en: "Aggressive" }, color: "text-red-400" },
];

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface CoPilotPanelProps {
  open: boolean;
  onClose: () => void;
  state: CoPilotState;
  sendMessage: (text: string) => void;
  setRiskProfile: (p: RiskProfile) => void;
  setLocale: (l: Locale) => void;
  clearHistory: () => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function CoPilotPanel({
  open,
  onClose,
  state,
  sendMessage,
  setRiskProfile,
  setLocale,
  clearHistory,
}: CoPilotPanelProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    if (open) {
      setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    }
  }, [state.messages.length, state.isTyping, open]);

  // Focus input when opened
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 300);
    }
  }, [open]);

  // Escape to close
  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [open, onClose]);

  const handleSend = useCallback(() => {
    const text = inputRef.current?.value?.trim();
    if (!text) return;
    sendMessage(text);
    if (inputRef.current) inputRef.current.value = "";
  }, [sendMessage]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  const locale = state.locale;
  const confPct = (state.confidence * 100).toFixed(0);
  const confColor = state.confidence > 0.6 ? "bg-green-500" : state.confidence > 0.3 ? "bg-yellow-500" : "bg-red-500";
  const rrColor = state.riskReward.rating === "good" ? "text-green-400" : state.riskReward.rating === "neutral" ? "text-yellow-400" : "text-red-400";

  return (
    <>
      {/* Backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm md:hidden"
          onClick={onClose}
        />
      )}

      {/* Panel */}
      <div
        ref={panelRef}
        className={`fixed top-0 right-0 z-50 h-full w-full sm:w-96 bg-black/80 backdrop-blur-2xl border-l border-white/10 shadow-2xl
          flex flex-col transition-transform duration-300 ease-in-out
          ${open ? "translate-x-0" : "translate-x-full"}`}
      >
        {/* Header */}
        <div className="flex items-center gap-2 px-4 py-3 border-b border-white/10 shrink-0">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-600/20">
            <Bot className="h-4 w-4 text-blue-400" />
          </div>
          <span className="text-sm font-semibold text-white flex-1">JARVIS Co-Pilot</span>
          {/* Locale toggle */}
          <button
            onClick={() => setLocale(locale === "de" ? "en" : "de")}
            className="px-1.5 py-0.5 rounded text-[10px] font-bold border border-white/10 text-white/60 hover:text-white hover:border-white/20 transition-colors"
          >
            {locale === "de" ? "DE" : "EN"}
          </button>
          {/* Clear */}
          {state.messages.length > 0 && (
            <button
              onClick={clearHistory}
              className="p-1 text-white/40 hover:text-red-400 transition-colors"
              title={locale === "de" ? "Chat loeschen" : "Clear chat"}
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          )}
          <button
            onClick={onClose}
            className="p-1 text-white/40 hover:text-white transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Risk Profile + Stats Bar */}
        <div className="px-4 py-2 border-b border-white/5 shrink-0 space-y-2">
          {/* Risk Profile */}
          <div className="flex items-center gap-1">
            {RISK_PROFILES.map((rp) => (
              <button
                key={rp.id}
                onClick={() => setRiskProfile(rp.id)}
                className={`flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium transition-colors ${
                  state.riskProfile === rp.id
                    ? `bg-white/10 ${rp.color} border border-white/10`
                    : "text-white/40 hover:text-white/70 border border-transparent"
                }`}
              >
                <rp.icon className="h-2.5 w-2.5" />
                {rp.label[locale]}
              </button>
            ))}
          </div>
          {/* Confidence + R:R */}
          <div className="flex items-center gap-3 text-[10px]">
            <div className="flex items-center gap-1.5">
              <span className="text-white/40">{locale === "de" ? "Konfidenz" : "Confidence"}:</span>
              <div className="w-16 h-1.5 rounded-full bg-white/10 overflow-hidden">
                <div className={`h-full rounded-full ${confColor}`} style={{ width: `${confPct}%` }} />
              </div>
              <span className="text-white/70 font-mono">{confPct}%</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-white/40">R:R:</span>
              <span className={`font-mono font-bold ${rrColor}`}>1:{state.riskReward.ratio.toFixed(1)}</span>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
          {state.messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-600/20">
                <Bot className="h-6 w-6 text-blue-400" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white mb-1">JARVIS Co-Pilot</h3>
                <p className="text-[11px] text-white/50 max-w-[250px]">
                  {locale === "de"
                    ? "Dein AI Trading-Assistent. Frag mich zu Maerkten, Strategien oder Risiko."
                    : "Your AI trading assistant. Ask about markets, strategies, or risk."}
                </p>
              </div>
              {/* Quick Actions */}
              <div className="flex flex-wrap gap-1.5 justify-center max-w-[280px]">
                {QUICK_ACTIONS.map((qa) => (
                  <button
                    key={qa.icon}
                    onClick={() => sendMessage(qa.prompt[locale])}
                    className="flex items-center gap-1 px-2 py-1 rounded-lg bg-white/5 border border-white/10 text-[10px] text-white/60 hover:text-white hover:bg-white/10 transition-colors"
                  >
                    <span>{qa.icon}</span>
                    <span>{qa.label[locale]}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {state.messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  {msg.role === "assistant" && (
                    <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-blue-600/20 mt-0.5">
                      <Bot className="h-3 w-3 text-blue-400" />
                    </div>
                  )}
                  <div
                    className={`max-w-[80%] rounded-lg px-3 py-2 text-[11px] leading-relaxed ${
                      msg.role === "user"
                        ? "bg-blue-600/20 text-white"
                        : "bg-white/5 text-white/90"
                    }`}
                  >
                    {msg.role === "assistant" ? (
                      <div
                        className="prose prose-sm prose-invert max-w-none [&_h1]:text-sm [&_h2]:text-xs [&_h2]:font-bold [&_h2]:mt-1 [&_h2]:mb-1 [&_h3]:text-[11px] [&_h3]:font-bold [&_p]:text-[11px] [&_li]:text-[11px] [&_code]:text-[10px] [&_strong]:text-white [&_br]:leading-tight"
                        dangerouslySetInnerHTML={{ __html: simpleMarkdown(msg.content) }}
                      />
                    ) : (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    )}
                  </div>
                  {msg.role === "user" && (
                    <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-white/10 mt-0.5">
                      <User className="h-3 w-3 text-white/60" />
                    </div>
                  )}
                </div>
              ))}
              {/* Typing Indicator */}
              {state.isTyping && (
                <div className="flex gap-2">
                  <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-blue-600/20 mt-0.5">
                    <Bot className="h-3 w-3 text-blue-400" />
                  </div>
                  <div className="rounded-lg bg-white/5 px-3 py-2">
                    <div className="flex gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: "0ms" }} />
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: "150ms" }} />
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: "300ms" }} />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Quick Actions Row (when messages exist) */}
        {state.messages.length > 0 && (
          <div className="px-4 py-1.5 border-t border-white/5 shrink-0">
            <div className="flex gap-1 overflow-x-auto no-scrollbar">
              {QUICK_ACTIONS.slice(0, 4).map((qa) => (
                <button
                  key={qa.icon}
                  onClick={() => sendMessage(qa.prompt[locale])}
                  className="flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-white/5 text-[9px] text-white/40 hover:text-white/70 transition-colors whitespace-nowrap shrink-0"
                >
                  <span>{qa.icon}</span>
                  <span>{qa.label[locale]}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="px-4 py-3 border-t border-white/10 shrink-0">
          <div className="flex gap-2">
            <textarea
              ref={inputRef}
              onKeyDown={handleKeyDown}
              placeholder={locale === "de" ? "Frag JARVIS..." : "Ask JARVIS..."}
              rows={1}
              className="flex-1 resize-none rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-[12px] text-white placeholder:text-white/30 focus:outline-none focus:ring-1 focus:ring-blue-500/50"
            />
            <button
              onClick={handleSend}
              disabled={state.isTyping}
              className="shrink-0 h-9 w-9 flex items-center justify-center rounded-lg bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 transition-colors"
            >
              <Send className="h-3.5 w-3.5" />
            </button>
          </div>
          <div className="mt-1.5 text-[9px] text-white/20 text-center">
            JARVIS Offline Mode — {locale === "de" ? "Regelbasierte Analyse" : "Rule-based analysis"}
          </div>
        </div>
      </div>
    </>
  );
}
