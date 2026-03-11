// =============================================================================
// src/app/(app)/chat/page.tsx — AI Chat with JARVIS
// =============================================================================

"use client";

import { useCallback, useRef, useState } from "react";
import { AppHeader } from "@/components/layout/app-header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useSystemStatus } from "@/hooks/use-jarvis";
import { usePortfolio } from "@/hooks/use-portfolio";
import { inferRegime } from "@/lib/types";
import { Send, Bot, User, Loader2, Sparkles, Trash2 } from "lucide-react";

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
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const { status } = useSystemStatus(10000);
  const { state: portfolio, totalValue, drawdown } = usePortfolio();
  const regime = status ? inferRegime(status.modus) : "RISK_ON";

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
    <>
      <AppHeader title="AI Chat" subtitle="Ask JARVIS" />
      <div className="flex flex-col h-[calc(100vh-3.5rem-2.5rem)] p-6">
        {/* Chat Area */}
        <Card className="bg-card/50 border-border/50 flex-1 flex flex-col overflow-hidden">
          <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center space-y-6">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-600/20">
                  <Sparkles className="h-8 w-8 text-blue-400" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white mb-1">
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
                      className="text-xs px-3 py-1.5 rounded-full bg-background/50 border border-border/50 text-muted-foreground hover:text-white hover:border-blue-500/30 transition-colors"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                  <Badge variant="outline" className="text-[10px]">
                    Regime: {regime.replace("_", " ")}
                  </Badge>
                  <Badge variant="outline" className="text-[10px]">
                    Positions: {portfolio.positions.length}
                  </Badge>
                  <Badge variant="outline" className="text-[10px]">
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
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-600/20">
                        <Bot className="h-4 w-4 text-blue-400" />
                      </div>
                    )}
                    <div
                      className={`max-w-[75%] rounded-lg px-4 py-3 text-sm ${
                        msg.role === "user"
                          ? "bg-blue-600/20 text-white"
                          : "bg-background/50 text-foreground"
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
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                        <User className="h-4 w-4 text-muted-foreground" />
                      </div>
                    )}
                  </div>
                ))}
                {loading && (
                  <div className="flex gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-600/20">
                      <Bot className="h-4 w-4 text-blue-400" />
                    </div>
                    <div className="rounded-lg bg-background/50 px-4 py-3">
                      <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </CardContent>

          {/* Input Area */}
          <div className="border-t border-border/50 p-4">
            <div className="flex gap-2">
              {messages.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="shrink-0 h-10 w-10 p-0 text-muted-foreground hover:text-red-400"
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
                className="flex-1 resize-none rounded-lg border border-border/50 bg-background/50 px-4 py-2.5 text-sm text-white placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-blue-500/50"
              />
              <Button
                onClick={() => sendMessage(input)}
                disabled={!input.trim() || loading}
                className="shrink-0 h-10 bg-blue-600 hover:bg-blue-700 text-white"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
            <div className="mt-2 text-[10px] text-muted-foreground text-center">
              JARVIS AI — Research & Analysis Tool. Not financial advice.
            </div>
          </div>
        </Card>
      </div>
    </>
  );
}

// Simple markdown to HTML (handles headings, bold, italic, lists, tables, code, hr)
function simpleMarkdown(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/^### (.+)$/gm, '<h3 class="font-bold mt-3 mb-1">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 class="font-bold mt-3 mb-2">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 class="font-bold text-lg mt-3 mb-2">$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, '<code class="bg-muted px-1 rounded text-xs">$1</code>')
    .replace(/^---$/gm, '<hr class="border-border/50 my-3" />')
    .replace(/^- (.+)$/gm, '<li class="ml-4">$1</li>')
    .replace(/^\d+\. (.+)$/gm, '<li class="ml-4 list-decimal">$1</li>')
    .replace(
      /\|(.+)\|/g,
      (match) => {
        const cells = match.split("|").filter(Boolean).map((c) => c.trim());
        if (cells.every((c) => /^[-:]+$/.test(c))) return "";
        const tag = match.includes("---") ? "td" : "td";
        return `<tr>${cells.map((c) => `<${tag} class="border border-border/30 px-2 py-1">${c}</${tag}>`).join("")}</tr>`;
      }
    )
    .replace(/(<tr>.*<\/tr>\n?)+/g, (match) => `<table class="w-full border-collapse my-2">${match}</table>`)
    .replace(/\n/g, "<br />");
}
