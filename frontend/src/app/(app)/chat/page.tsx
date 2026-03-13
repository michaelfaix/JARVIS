// =============================================================================
// src/app/(app)/chat/page.tsx — AI Chat with JARVIS
// =============================================================================

"use client";

import { useCallback, useRef, useState } from "react";
import { HudPanel } from "@/components/ui/hud-panel";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useSystemStatus } from "@/hooks/use-jarvis";
import { usePortfolio } from "@/hooks/use-portfolio";
import { useProfile } from "@/hooks/use-profile";
import { UpgradeGate } from "@/components/ui/upgrade-gate";
import { Send, Bot, User, Loader2, Sparkles, Trash2 } from "lucide-react";
import { ApiOfflineBanner } from "@/components/ui/api-offline-banner";
import { simpleMarkdown } from "@/lib/markdown";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

const QUICK_PROMPTS = [
  "What does the current market regime mean?",
  "How do I interpret OOD warnings?",
  "What's a safe position size for BTC?",
  "Explain the momentum vs mean reversion strategy",
  "How does JARVIS calculate confidence scores?",
];

export default function ChatPage() {
  const { tier } = useProfile();

  return (
    <UpgradeGate currentTier={tier} requiredTier="pro" feature="AI Chat Assistant">
      <ChatContent />
    </UpgradeGate>
  );
}

function ChatContent() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const { status, regime, error: statusError } = useSystemStatus(10000);
  const { state: portfolio, totalValue, drawdown } = usePortfolio();

  const buildContext = useCallback(() => {
    const parts: string[] = [];
    if (status) {
      parts.push(`System Modus: ${status.modus}`);
      parts.push(`Market Regime: ${regime}`);
      parts.push(`ECE: ${status.ece.toFixed(4)}, OOD Score: ${status.ood_score.toFixed(3)}`);
      parts.push(`Meta-Uncertainty: ${status.meta_unsicherheit.toFixed(3)}`);
    }
    parts.push(`Portfolio Value: $${totalValue.toFixed(0)}`);
    parts.push(`Open Positions: ${portfolio.positions.length}`);
    parts.push(`Realized P&L: $${portfolio.realizedPnl.toFixed(0)}`);
    parts.push(`Drawdown: ${drawdown.toFixed(2)}%`);
    if (portfolio.positions.length > 0) {
      parts.push(`Positions: ${portfolio.positions.map((p) => `${p.asset} ${p.direction}`).join(", ")}`);
    }
    return parts.join("\n");
  }, [status, regime, totalValue, portfolio, drawdown]);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || loading) return;

      const userMsg: Message = {
        id: `user-${Date.now()}`,
        role: "user",
        content: text.trim(),
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setInput("");
      setLoading(true);

      try {
        const allMessages = [...messages, userMsg].map((m) => ({
          role: m.role,
          content: m.content,
        }));

        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            messages: allMessages,
            context: buildContext(),
          }),
        });

        const data = await res.json();
        const assistantMsg: Message = {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: data.response ?? data.error ?? "No response",
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, assistantMsg]);
      } catch {
        setMessages((prev) => [
          ...prev,
          {
            id: `error-${Date.now()}`,
            role: "assistant",
            content: "Connection error. Make sure the frontend dev server is running.",
            timestamp: new Date(),
          },
        ]);
      } finally {
        setLoading(false);
        setTimeout(() => {
          messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
        }, 100);
      }
    },
    [messages, loading, buildContext]
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem-2.5rem)] p-2 sm:p-3 md:p-4 gap-3">
      {statusError && <ApiOfflineBanner />}
      {/* Chat Area */}
      <HudPanel title="JARVIS COMMS" scanLine className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center space-y-6">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-hud-cyan/20">
                <Sparkles className="h-8 w-8 text-hud-cyan" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white mb-1 font-mono">
                  JARVIS AI Assistant
                </h3>
                <p className="text-sm text-muted-foreground max-w-md">
                  Ask questions about markets, signals, risk management, or
                  trading strategies. JARVIS has context about your current
                  portfolio and market regime.
                </p>
              </div>
              <div className="flex flex-wrap gap-2 justify-center max-w-lg">
                {QUICK_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => sendMessage(prompt)}
                    className="text-xs px-3 py-1.5 rounded-full bg-hud-bg/60 border border-hud-border/30 text-muted-foreground hover:text-hud-cyan hover:border-hud-cyan/30 transition-colors"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                <Badge variant="outline" className="text-[10px] border-hud-border/30 text-hud-cyan">
                  Regime: {regime.replace("_", " ")}
                </Badge>
                <Badge variant="outline" className="text-[10px] border-hud-border/30 text-hud-cyan">
                  Positions: {portfolio.positions.length}
                </Badge>
                <Badge variant="outline" className="text-[10px] border-hud-border/30 text-hud-cyan">
                  Portfolio: ${totalValue.toLocaleString("en-US", { maximumFractionDigits: 0 })}
                </Badge>
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-3 ${
                    msg.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  {msg.role === "assistant" && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-hud-cyan/20">
                      <Bot className="h-4 w-4 text-hud-cyan" />
                    </div>
                  )}
                  <div
                    className={`max-w-[75%] rounded-lg px-4 py-3 text-sm ${
                      msg.role === "user"
                        ? "bg-hud-cyan/15 text-white border border-hud-cyan/20"
                        : "bg-hud-bg/60 text-foreground border border-hud-border/30"
                    }`}
                  >
                    {msg.role === "assistant" ? (
                      <div
                        className="prose prose-sm prose-invert max-w-none [&_table]:text-xs [&_th]:px-2 [&_td]:px-2 [&_h2]:text-base [&_h2]:mt-0 [&_h3]:text-sm [&_p]:text-sm [&_li]:text-sm [&_code]:text-xs"
                        dangerouslySetInnerHTML={{
                          __html: simpleMarkdown(msg.content),
                        }}
                      />
                    ) : (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    )}
                  </div>
                  {msg.role === "user" && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-hud-bg/60 border border-hud-border/30">
                      <User className="h-4 w-4 text-muted-foreground" />
                    </div>
                  )}
                </div>
              ))}
              {loading && (
                <div className="flex gap-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-hud-cyan/20">
                    <Bot className="h-4 w-4 text-hud-cyan" />
                  </div>
                  <div className="rounded-lg bg-hud-bg/60 border border-hud-border/30 px-4 py-3">
                    <Loader2 className="h-4 w-4 animate-spin text-hud-cyan" />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t border-hud-border p-3 sm:p-4">
          <div className="flex gap-2">
            {messages.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="shrink-0 h-10 w-10 p-0 text-muted-foreground hover:text-hud-red"
                onClick={() => setMessages([])}
                title="Clear chat"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask JARVIS about markets, signals, or risk..."
              rows={1}
              className="flex-1 resize-none rounded-lg border border-hud-border/50 bg-hud-bg/60 px-4 py-2.5 text-sm text-white font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-hud-cyan/50"
            />
            <Button
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || loading}
              className="shrink-0 h-10 bg-hud-cyan/20 hover:bg-hud-cyan/30 text-hud-cyan border border-hud-cyan/30"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
          <div className="mt-2 text-[10px] text-muted-foreground text-center font-mono">
            JARVIS AI — Research & Analysis Tool. Not financial advice.
          </div>
        </div>
      </HudPanel>
    </div>
  );
}
