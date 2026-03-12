// =============================================================================
// src/components/onboarding/welcome-flow.tsx — First-time user onboarding flow
// =============================================================================

"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  TrendingUp,
  CandlestickChart,
  Radio,
  Wallet,
  Sparkles,
  Target,
  BarChart3,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";

const STORAGE_KEY = "jarvis-onboarding-done";

// ---------------------------------------------------------------------------
// Asset chips for Step 2
// ---------------------------------------------------------------------------
const ASSETS = [
  { symbol: "BTC", label: "Bitcoin", color: "text-orange-400" },
  { symbol: "ETH", label: "Ethereum", color: "text-purple-400" },
  { symbol: "SOL", label: "Solana", color: "text-cyan-400" },
  { symbol: "SPY", label: "S&P 500", color: "text-green-400" },
  { symbol: "AAPL", label: "Apple", color: "text-blue-400" },
  { symbol: "NVDA", label: "Nvidia", color: "text-lime-400" },
  { symbol: "TSLA", label: "Tesla", color: "text-red-400" },
  { symbol: "GLD", label: "Gold", color: "text-yellow-400" },
] as const;

// ---------------------------------------------------------------------------
// Explore cards for Step 3
// ---------------------------------------------------------------------------
const EXPLORE_CARDS = [
  {
    title: "Dashboard",
    description: "See market signals and regime detection",
    icon: TrendingUp,
    href: "/",
  },
  {
    title: "Charts",
    description: "Live charts with technical indicators",
    icon: CandlestickChart,
    href: "/charts",
  },
  {
    title: "Signals",
    description: "AI-powered trading signals",
    icon: Radio,
    href: "/signals",
  },
  {
    title: "Portfolio",
    description: "Paper trade and track P&L",
    icon: Wallet,
    href: "/portfolio",
  },
] as const;

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export function WelcomeFlow() {
  const router = useRouter();
  const [visible, setVisible] = useState(false);
  const [step, setStep] = useState(0);
  const [direction, setDirection] = useState<"forward" | "backward">("forward");
  const [animating, setAnimating] = useState(false);
  const [selectedAssets, setSelectedAssets] = useState<Set<string>>(new Set());

  // Check localStorage on mount
  useEffect(() => {
    try {
      if (localStorage.getItem(STORAGE_KEY) !== "true") {
        setVisible(true);
      }
    } catch {
      // SSR or storage unavailable — don't show
    }
  }, []);

  const complete = useCallback(() => {
    try {
      localStorage.setItem(STORAGE_KEY, "true");
      if (selectedAssets.size > 0) {
        localStorage.setItem(
          "jarvis-preferred-assets",
          JSON.stringify(Array.from(selectedAssets))
        );
      }
    } catch {
      // ignore
    }
    setVisible(false);
  }, [selectedAssets]);

  const goTo = useCallback(
    (next: number) => {
      if (animating) return;
      setDirection(next > step ? "forward" : "backward");
      setAnimating(true);
      // Brief delay so the exit animation can run
      setTimeout(() => {
        setStep(next);
        setAnimating(false);
      }, 200);
    },
    [step, animating]
  );

  const toggleAsset = (symbol: string) => {
    setSelectedAssets((prev) => {
      const next = new Set(prev);
      if (next.has(symbol)) {
        next.delete(symbol);
      } else {
        next.add(symbol);
      }
      return next;
    });
  };

  if (!visible) return null;

  // -------------------------------------------------------------------------
  // Steps
  // -------------------------------------------------------------------------
  const steps = [
    // Step 1 — Welcome
    <div key="welcome" className="flex flex-col items-center text-center gap-6">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-600/20 ring-1 ring-blue-500/30">
        <Sparkles className="h-8 w-8 text-blue-400" />
      </div>

      <div>
        <h2 className="text-2xl font-bold text-white">
          Welcome to JARVIS Trader
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Your AI-powered trading intelligence platform
        </p>
      </div>

      <div className="w-full space-y-3 text-left">
        {[
          {
            icon: Target,
            text: "Real-time AI signals for crypto, forex & stocks",
          },
          {
            icon: Wallet,
            text: "Paper trade risk-free with $10,000 virtual capital",
          },
          {
            icon: BarChart3,
            text: "Track performance with advanced analytics",
          },
        ].map(({ icon: Icon, text }) => (
          <div
            key={text}
            className="flex items-center gap-3 rounded-lg border border-border/50 bg-background/50 px-4 py-3"
          >
            <Icon className="h-5 w-5 shrink-0 text-blue-400" />
            <span className="text-sm text-white/90">{text}</span>
          </div>
        ))}
      </div>

      <button
        onClick={() => goTo(1)}
        className="mt-2 w-full rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
      >
        Get Started
      </button>
    </div>,

    // Step 2 — Quick Setup
    <div key="setup" className="flex flex-col items-center text-center gap-6">
      <div>
        <h2 className="text-xl font-bold text-white">Choose Your Focus</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Select 2-3 assets you&apos;re most interested in
        </p>
      </div>

      <div className="grid w-full grid-cols-2 gap-2.5">
        {ASSETS.map(({ symbol, label, color }) => {
          const active = selectedAssets.has(symbol);
          return (
            <button
              key={symbol}
              onClick={() => toggleAsset(symbol)}
              className={cn(
                "flex items-center gap-2.5 rounded-lg border px-4 py-3 text-left transition-all",
                active
                  ? "border-blue-500 bg-blue-600/10"
                  : "border-border/40 bg-background/30 opacity-60 hover:opacity-90"
              )}
            >
              <span
                className={cn(
                  "text-sm font-bold",
                  active ? color : "text-muted-foreground"
                )}
              >
                {symbol}
              </span>
              <span className="text-xs text-muted-foreground">{label}</span>
            </button>
          );
        })}
      </div>

      <div className="flex w-full gap-3">
        <button
          onClick={() => goTo(2)}
          className="flex-1 rounded-lg border border-border/50 px-4 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:text-white"
        >
          Skip
        </button>
        <button
          onClick={() => goTo(2)}
          className="flex-1 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
        >
          Continue
        </button>
      </div>
    </div>,

    // Step 3 — Explore
    <div key="explore" className="flex flex-col items-center text-center gap-6">
      <div>
        <h2 className="text-xl font-bold text-white">
          Here&apos;s What You Can Do
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Explore the core features of JARVIS Trader
        </p>
      </div>

      <div className="w-full space-y-2.5">
        {EXPLORE_CARDS.map(({ title, description, icon: Icon, href }) => (
          <button
            key={title}
            onClick={() => {
              complete();
              router.push(href);
            }}
            className="flex w-full items-center gap-3 rounded-lg border border-border/50 bg-background/50 px-4 py-3 text-left transition-colors hover:border-blue-500/50 hover:bg-blue-600/5"
          >
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-600/15">
              <Icon className="h-4.5 w-4.5 text-blue-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white">{title}</p>
              <p className="text-xs text-muted-foreground">{description}</p>
            </div>
            <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
          </button>
        ))}
      </div>

      <button
        onClick={complete}
        className="mt-2 w-full rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
      >
        Start Trading
      </button>
    </div>,
  ];

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="relative mx-4 w-full max-w-lg rounded-2xl border border-border/50 bg-card p-8 shadow-2xl">
        {/* Dismiss button */}
        <button
          onClick={complete}
          className="absolute right-4 top-4 text-muted-foreground transition-colors hover:text-white"
          aria-label="Close onboarding"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>

        {/* Step content with transition */}
        <div
          className={cn(
            "transition-all duration-200 ease-in-out",
            animating
              ? direction === "forward"
                ? "translate-x-4 opacity-0"
                : "-translate-x-4 opacity-0"
              : "translate-x-0 opacity-100"
          )}
        >
          {steps[step]}
        </div>

        {/* Step indicators */}
        <div className="mt-6 flex items-center justify-center gap-2">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className={cn(
                "h-1.5 rounded-full transition-all duration-300",
                i === step
                  ? "w-6 bg-blue-500"
                  : "w-1.5 bg-border/80"
              )}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
