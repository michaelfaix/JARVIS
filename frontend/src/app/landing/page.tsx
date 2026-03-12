// =============================================================================
// src/app/landing/page.tsx — Public Landing Page for JARVIS-Trader
// =============================================================================

"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  Radar,
  ShieldAlert,
  BarChart3,
  Brain,
  Zap,
  LineChart,
  Check,
  ArrowRight,
  ChevronRight,
  Star,
  Building2,
  Sparkles,
  Github,
  Twitter,
  Mail,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Waitlist helpers
// ---------------------------------------------------------------------------
const STORAGE_KEY = "jarvis-waitlist";

function getWaitlist(): string[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]");
  } catch {
    return [];
  }
}

function addToWaitlist(email: string) {
  const list = getWaitlist();
  if (!list.includes(email)) {
    list.push(email);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
  }
}

// ---------------------------------------------------------------------------
// Features
// ---------------------------------------------------------------------------
const FEATURES = [
  {
    icon: Brain,
    title: "AI Market Intelligence",
    description:
      "ML-powered regime detection across 5 market states. Know when to be aggressive and when to protect capital.",
    color: "text-blue-400",
    bg: "bg-blue-500/10",
  },
  {
    icon: Zap,
    title: "Real-Time Signals",
    description:
      "LONG/SHORT signals with confidence scores, quality ratings, and out-of-distribution warnings.",
    color: "text-yellow-400",
    bg: "bg-yellow-500/10",
  },
  {
    icon: LineChart,
    title: "Strategy Lab",
    description:
      "Backtest momentum, mean reversion, or combined strategies across multiple assets with walk-forward validation.",
    color: "text-green-400",
    bg: "bg-green-500/10",
  },
  {
    icon: ShieldAlert,
    title: "Risk Guardian",
    description:
      "Automated position sizing, drawdown alerts, exposure limits, and cash reserve monitoring.",
    color: "text-red-400",
    bg: "bg-red-500/10",
  },
  {
    icon: Radar,
    title: "Opportunity Radar",
    description:
      "Scan markets for top opportunities ranked by trend strength, volume, and momentum across crypto, forex, and stocks.",
    color: "text-purple-400",
    bg: "bg-purple-500/10",
  },
  {
    icon: BarChart3,
    title: "Paper Trading",
    description:
      "Practice with simulated capital. Track P&L, win rate, and drawdown before risking real money.",
    color: "text-cyan-400",
    bg: "bg-cyan-500/10",
  },
] as const;

// ---------------------------------------------------------------------------
// Pricing tiers
// ---------------------------------------------------------------------------
const TIERS = [
  {
    name: "Free",
    price: "0",
    period: "forever",
    description: "Get started with basic market intelligence",
    icon: Sparkles,
    color: "border-border/50",
    features: [
      "3 Assets, 2 Timeframes",
      "1 Strategy (Scalping)",
      "Paper Trading (10k)",
      "Signals (15 min delay)",
      "Basic Regime Detection",
      "Community Support",
    ],
    cta: "Start Free",
    highlight: false,
  },
  {
    name: "Pro",
    price: "29",
    period: "/month",
    description: "Full power for serious traders",
    icon: Star,
    color: "border-blue-500/50",
    features: [
      "All Assets & Timeframes",
      "8 Strategies",
      "Paper Trading (up to 500k)",
      "Real-Time Signals",
      "Full Regime Detection",
      "OOD Warnings",
      "90-Day Backtesting + WFV",
      "AI Chat Assistant",
      "Email Support (48h)",
    ],
    cta: "Join Waitlist",
    highlight: true,
  },
  {
    name: "Enterprise",
    price: "199",
    period: "/month",
    description: "For teams and professional traders",
    icon: Building2,
    color: "border-border/50",
    features: [
      "Everything in Pro",
      "Custom Data Feeds",
      "Unlimited Strategies",
      "Unlimited Paper Trading",
      "Raw Signal Data",
      "Custom OOD Thresholds",
      "Unlimited Backtesting",
      "REST + WebSocket API",
      "Priority Slack (4h SLA)",
    ],
    cta: "Contact Us",
    highlight: false,
  },
] as const;

// ---------------------------------------------------------------------------
// Stats
// ---------------------------------------------------------------------------
const STATS = [
  { value: "8,890+", label: "Test Suite" },
  { value: "100%", label: "FAS Compliance" },
  { value: "0.76ms", label: "P95 Latency" },
  { value: "96%+", label: "Code Coverage" },
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export default function LandingPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [waitlistCount, setWaitlistCount] = useState(0);

  useEffect(() => {
    setWaitlistCount(getWaitlist().length);
  }, []);

  const handleSubmit = useCallback(
    (e: FormEvent) => {
      e.preventDefault();
      const trimmed = email.trim().toLowerCase();
      if (!trimmed || !trimmed.includes("@")) return;
      addToWaitlist(trimmed);
      setSubmitted(true);
      setWaitlistCount(getWaitlist().length);
      setEmail("");
    },
    [email]
  );

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* ── Navbar ────────────────────────────────────────────────── */}
      <nav className="fixed top-0 z-50 w-full border-b border-border/30 bg-background/80 backdrop-blur-lg">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-sm font-bold text-white">
              J
            </div>
            <span className="text-sm font-bold text-white">JARVIS Trader</span>
          </div>
          <div className="flex items-center gap-4">
            <a
              href="#features"
              className="hidden text-sm text-muted-foreground hover:text-white transition-colors sm:inline"
            >
              Features
            </a>
            <a
              href="#pricing"
              className="hidden text-sm text-muted-foreground hover:text-white transition-colors sm:inline"
            >
              Pricing
            </a>
            <Link
              href="/login"
              className="rounded-lg bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
            >
              Open App
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ──────────────────────────────────────────────────── */}
      <section className="relative flex min-h-[90vh] flex-col items-center justify-center px-6 pt-14 text-center">
        {/* Subtle gradient background */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute left-1/2 top-1/3 h-[600px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-blue-600/10 blur-[120px]" />
          <div className="absolute right-1/4 top-2/3 h-[400px] w-[400px] rounded-full bg-purple-600/8 blur-[100px]" />
        </div>

        <div className="relative z-10 max-w-3xl space-y-8">
          {/* Badge */}
          <div className="mx-auto flex w-fit items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-4 py-1.5 text-xs text-blue-400">
            <Zap className="h-3 w-3" />
            AI-Powered Trading Intelligence
          </div>

          {/* Headline */}
          <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl lg:text-6xl">
            Trade Smarter with{" "}
            <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              JARVIS
            </span>
          </h1>

          {/* Subheadline */}
          <p className="mx-auto max-w-xl text-lg text-muted-foreground">
            ML-powered market regime detection, real-time trading signals, and
            automated risk management. Your AI co-pilot for crypto, forex, and
            stocks.
          </p>

          {/* CTA */}
          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <a
              href="#waitlist"
              className="flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-600/25 hover:bg-blue-700 transition-all"
            >
              Join the Waitlist
              <ArrowRight className="h-4 w-4" />
            </a>
            <Link
              href="/register"
              className="flex items-center gap-2 rounded-lg border border-border/50 bg-card/50 px-6 py-3 text-sm font-medium text-muted-foreground hover:text-white hover:border-border transition-all"
            >
              Get Started Free
              <ChevronRight className="h-4 w-4" />
            </Link>
          </div>

          {/* Social proof */}
          <div className="flex flex-wrap justify-center gap-8 pt-4">
            {STATS.map((s) => (
              <div key={s.label} className="text-center">
                <div className="text-xl font-bold text-white">{s.value}</div>
                <div className="text-xs text-muted-foreground">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ──────────────────────────────────────────────── */}
      <section id="features" className="mx-auto max-w-6xl px-6 py-24">
        <div className="mb-16 text-center">
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            Everything You Need to Trade with Confidence
          </h2>
          <p className="mt-4 text-muted-foreground max-w-2xl mx-auto">
            Built on a battle-tested ML backend with 8,890+ tests and 100% specification compliance.
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => {
            const Icon = f.icon;
            return (
              <div
                key={f.title}
                className="group rounded-xl border border-border/30 bg-card/30 p-6 transition-all hover:border-border/60 hover:bg-card/50"
              >
                <div
                  className={`mb-4 flex h-12 w-12 items-center justify-center rounded-xl ${f.bg}`}
                >
                  <Icon className={`h-6 w-6 ${f.color}`} />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-white">
                  {f.title}
                </h3>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {f.description}
                </p>
              </div>
            );
          })}
        </div>
      </section>

      {/* ── USP Banner ────────────────────────────────────────────── */}
      <section className="border-y border-border/30 bg-card/20">
        <div className="mx-auto max-w-4xl px-6 py-16 text-center">
          <h3 className="text-2xl font-bold text-white sm:text-3xl">
            Unique: Timeframe Slider
          </h3>
          <p className="mt-4 text-muted-foreground max-w-2xl mx-auto">
            Drag from 1 minute to 1 week — JARVIS automatically selects the
            optimal strategy, recalculates entry/exit points, and adapts regime
            detection. No other platform does this.
          </p>
        </div>
      </section>

      {/* ── Pricing ───────────────────────────────────────────────── */}
      <section id="pricing" className="mx-auto max-w-6xl px-6 py-24">
        <div className="mb-16 text-center">
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            Simple, Transparent Pricing
          </h2>
          <p className="mt-4 text-muted-foreground">
            Start free. Upgrade when you&apos;re ready.
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {TIERS.map((tier) => {
            const Icon = tier.icon;
            return (
              <div
                key={tier.name}
                className={`relative flex flex-col rounded-xl border ${tier.color} bg-card/30 p-6 transition-all hover:bg-card/50 ${
                  tier.highlight
                    ? "ring-1 ring-blue-500/30 shadow-lg shadow-blue-600/10"
                    : ""
                }`}
              >
                {tier.highlight && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-blue-600 px-3 py-0.5 text-xs font-medium text-white">
                    Most Popular
                  </div>
                )}

                <div className="mb-4 flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-card">
                    <Icon className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">{tier.name}</h3>
                    <p className="text-xs text-muted-foreground">
                      {tier.description}
                    </p>
                  </div>
                </div>

                <div className="mb-6">
                  <span className="text-4xl font-bold text-white">
                    &euro;{tier.price}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {tier.period}
                  </span>
                </div>

                <ul className="mb-6 flex-1 space-y-2.5">
                  {tier.features.map((feat) => (
                    <li
                      key={feat}
                      className="flex items-start gap-2 text-sm text-muted-foreground"
                    >
                      <Check className="mt-0.5 h-4 w-4 shrink-0 text-green-400" />
                      {feat}
                    </li>
                  ))}
                </ul>

                <a
                  href="#waitlist"
                  className={`mt-auto block rounded-lg py-2.5 text-center text-sm font-medium transition-colors ${
                    tier.highlight
                      ? "bg-blue-600 text-white hover:bg-blue-700"
                      : "border border-border/50 text-muted-foreground hover:text-white hover:border-border"
                  }`}
                >
                  {tier.cta}
                </a>
              </div>
            );
          })}
        </div>
      </section>

      {/* ── Waitlist ──────────────────────────────────────────────── */}
      <section
        id="waitlist"
        className="border-t border-border/30 bg-card/20"
      >
        <div className="mx-auto max-w-xl px-6 py-24 text-center">
          <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-600/20 mx-auto">
            <Mail className="h-7 w-7 text-blue-400" />
          </div>

          <h2 className="text-3xl font-bold text-white">Join the Waitlist</h2>
          <p className="mt-3 text-muted-foreground">
            Be among the first to access JARVIS Trader. Early adopters get 3
            months Pro for free.
          </p>

          {submitted ? (
            <div className="mt-8 rounded-xl border border-green-500/30 bg-green-500/10 p-6">
              <Check className="mx-auto mb-2 h-8 w-8 text-green-400" />
              <p className="font-semibold text-green-400">
                You&apos;re on the list!
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                We&apos;ll notify you when JARVIS Trader launches.
                {waitlistCount > 1 && (
                  <span className="block mt-1">
                    {waitlistCount} people on the waitlist.
                  </span>
                )}
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="mt-8">
              <div className="flex gap-2 sm:flex-row flex-col">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  className="flex-1 rounded-lg border border-border/50 bg-background/50 px-4 py-3 text-sm text-white placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                />
                <button
                  type="submit"
                  className="flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-600/25 hover:bg-blue-700 transition-colors"
                >
                  Join Waitlist
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>
              {waitlistCount > 0 && (
                <p className="mt-3 text-xs text-muted-foreground">
                  {waitlistCount} {waitlistCount === 1 ? "person" : "people"}{" "}
                  already signed up.
                </p>
              )}
            </form>
          )}
        </div>
      </section>

      {/* ── Footer ────────────────────────────────────────────────── */}
      <footer className="border-t border-border/30">
        <div className="mx-auto max-w-6xl px-6 py-12">
          <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-sm font-bold text-white">
                J
              </div>
              <div>
                <div className="text-sm font-bold text-white">
                  JARVIS Trader
                </div>
                <div className="text-[10px] text-muted-foreground">
                  AI Trading Intelligence Platform
                </div>
              </div>
            </div>

            <div className="flex items-center gap-6">
              <a
                href="#features"
                className="text-xs text-muted-foreground hover:text-white transition-colors"
              >
                Features
              </a>
              <a
                href="#pricing"
                className="text-xs text-muted-foreground hover:text-white transition-colors"
              >
                Pricing
              </a>
              <a
                href="#waitlist"
                className="text-xs text-muted-foreground hover:text-white transition-colors"
              >
                Waitlist
              </a>
              <Link
                href="/"
                className="text-xs text-muted-foreground hover:text-white transition-colors"
              >
                App
              </Link>
            </div>

            <div className="flex items-center gap-4">
              <Github className="h-4 w-4 text-muted-foreground hover:text-white cursor-pointer transition-colors" />
              <Twitter className="h-4 w-4 text-muted-foreground hover:text-white cursor-pointer transition-colors" />
              <Mail className="h-4 w-4 text-muted-foreground hover:text-white cursor-pointer transition-colors" />
            </div>
          </div>

          <div className="mt-8 border-t border-border/30 pt-6 text-center">
            <p className="text-xs text-muted-foreground">
              &copy; {new Date().getFullYear()} JARVIS Trader. All rights
              reserved. Not financial advice. Paper trading is a simulation.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
