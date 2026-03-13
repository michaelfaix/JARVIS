// =============================================================================
// src/app/(app)/pricing/page.tsx — Pricing Page with 3 plan tiers
// =============================================================================

"use client";

import { HudPanel } from "@/components/ui/hud-panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useProfile, type Tier } from "@/hooks/use-profile";
import { useSubscription } from "@/hooks/use-subscription";
import { Check, Sparkles, Zap, Shield } from "lucide-react";

interface PlanDef {
  tier: Tier;
  name: string;
  price: string;
  period: string;
  icon: React.ReactNode;
  color: string;
  badgeClass: string;
  btnClass: string;
  borderClass: string;
  features: string[];
}

const PLANS: PlanDef[] = [
  {
    tier: "free",
    name: "Free",
    price: "\u20ac0",
    period: "/month",
    icon: <Shield className="h-5 w-5 text-zinc-400" />,
    color: "text-zinc-400",
    badgeClass: "bg-zinc-600/20 text-zinc-400 border-zinc-500/30",
    btnClass: "",
    borderClass: "",
    features: [
      "3 tracked assets",
      "\u20ac100K paper capital",
      "15-minute signal delay",
      "1 strategy",
      "Community support",
    ],
  },
  {
    tier: "pro",
    name: "Pro",
    price: "\u20ac29",
    period: "/Mo",
    icon: <Sparkles className="h-5 w-5 text-hud-cyan" />,
    color: "text-hud-cyan",
    badgeClass: "bg-hud-cyan/20 text-hud-cyan border-hud-cyan/30",
    btnClass:
      "bg-hud-cyan/20 hover:bg-hud-cyan/30 text-hud-cyan border border-hud-cyan/30",
    borderClass: "border-hud-cyan/40",
    features: [
      "Unlimited assets",
      "Up to \u20ac500K paper capital",
      "Real-time signals (no delay)",
      "Out-of-distribution detection",
      "Up to 8 strategies",
      "Priority support",
    ],
  },
  {
    tier: "enterprise",
    name: "Enterprise",
    price: "\u20ac199",
    period: "/Mo",
    icon: <Zap className="h-5 w-5 text-hud-amber" />,
    color: "text-hud-amber",
    badgeClass: "bg-hud-amber/20 text-hud-amber border-hud-amber/30",
    btnClass:
      "bg-hud-amber/20 hover:bg-hud-amber/30 text-hud-amber border border-hud-amber/30",
    borderClass: "border-hud-amber/40",
    features: [
      "Everything in Pro",
      "Unlimited paper capital",
      "Unlimited strategies",
      "Custom model training",
      "Dedicated infrastructure",
      "SLA & dedicated support",
    ],
  },
];

const tierRank: Record<Tier, number> = { free: 0, pro: 1, enterprise: 2 };

export default function PricingPage() {
  const { tier } = useProfile();
  const { subscribe, loading } = useSubscription();

  return (
    <div className="p-2 sm:p-3 md:p-4 space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="text-center space-y-1">
        <h1 className="text-2xl font-bold text-white font-mono">
          Choose Your Plan
        </h1>
        <p className="text-sm text-muted-foreground font-mono">
          Unlock powerful trading features with a premium subscription
        </p>
      </div>

      {/* Plan Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {PLANS.map((plan) => {
          const isCurrent = tier === plan.tier;
          const isDowngrade = tierRank[tier] > tierRank[plan.tier];
          const isUpgrade = tierRank[tier] < tierRank[plan.tier];

          return (
            <HudPanel
              key={plan.tier}
              className={`relative ${plan.borderClass}`}
            >
              {/* Highlight bar for Pro */}
              {plan.tier === "pro" && (
                <div className="absolute top-0 inset-x-0 h-0.5 bg-gradient-to-r from-hud-cyan to-blue-500" />
              )}
              {/* Highlight bar for Enterprise */}
              {plan.tier === "enterprise" && (
                <div className="absolute top-0 inset-x-0 h-0.5 bg-gradient-to-r from-hud-amber to-orange-500" />
              )}

              <div className="p-4 space-y-4">
                {/* Plan header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {plan.icon}
                    <span
                      className={`text-base font-semibold font-mono ${plan.color}`}
                    >
                      {plan.name}
                    </span>
                  </div>
                  {isCurrent && (
                    <Badge className={`text-[10px] ${plan.badgeClass}`}>
                      Current Plan
                    </Badge>
                  )}
                </div>

                {/* Price */}
                <div>
                  <span className="text-3xl font-bold text-white font-mono">
                    {plan.price}
                  </span>
                  <span className="text-sm text-muted-foreground font-mono">
                    {plan.period}
                  </span>
                </div>

                {/* Features */}
                <ul className="space-y-2 min-h-[180px]">
                  {plan.features.map((feature) => (
                    <li
                      key={feature}
                      className="flex items-start gap-2 text-sm text-muted-foreground font-mono"
                    >
                      <Check className="h-4 w-4 text-hud-green mt-0.5 shrink-0" />
                      {feature}
                    </li>
                  ))}
                </ul>

                {/* Action button */}
                {plan.tier === "free" ? (
                  <Button
                    variant="outline"
                    className="w-full border-hud-border text-muted-foreground font-mono"
                    disabled
                  >
                    {isCurrent ? "Current Plan" : "Included"}
                  </Button>
                ) : (
                  <Button
                    className={`w-full gap-2 font-mono ${
                      isUpgrade ? plan.btnClass : ""
                    }`}
                    variant={isCurrent || isDowngrade ? "outline" : "default"}
                    disabled={isCurrent || isDowngrade || loading}
                    onClick={() => subscribe(plan.tier as "pro" | "enterprise")}
                  >
                    {loading ? (
                      "Redirecting..."
                    ) : isCurrent ? (
                      "Current Plan"
                    ) : isDowngrade ? (
                      "Included in Your Plan"
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4" />
                        Upgrade to {plan.name}
                      </>
                    )}
                  </Button>
                )}
              </div>
            </HudPanel>
          );
        })}
      </div>

      {/* Footer */}
      <p className="text-center text-xs text-muted-foreground font-mono">
        Cancel anytime. Powered by Stripe for secure payments.
      </p>
    </div>
  );
}
