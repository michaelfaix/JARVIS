// =============================================================================
// src/components/upgrade/pricing-modal.tsx — Pricing / Upgrade modal
// =============================================================================

"use client";

import { useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useSubscription } from "@/hooks/use-subscription";
import { useProfile, type Tier } from "@/hooks/use-profile";
import { X, Check, Sparkles, Zap } from "lucide-react";

interface PricingModalProps {
  open: boolean;
  onClose: () => void;
}

interface PlanDef {
  tier: "pro" | "enterprise";
  name: string;
  price: string;
  period: string;
  icon: React.ReactNode;
  highlight: boolean;
  features: string[];
}

const PLANS: PlanDef[] = [
  {
    tier: "pro",
    name: "Pro",
    price: "\u20ac29",
    period: "/month",
    icon: <Sparkles className="h-5 w-5 text-blue-400" />,
    highlight: true,
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
    period: "/month",
    icon: <Zap className="h-5 w-5 text-purple-400" />,
    highlight: false,
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

export function PricingModal({ open, onClose }: PricingModalProps) {
  const { subscribe, loading } = useSubscription();
  const { tier } = useProfile();
  const backdropRef = useRef<HTMLDivElement>(null);

  // Close on Escape key
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;

  const tierRank: Record<Tier, number> = { free: 0, pro: 1, enterprise: 2 };

  return (
    <div
      ref={backdropRef}
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={(e) => {
        if (e.target === backdropRef.current) onClose();
      }}
    >
      <div className="relative w-full max-w-2xl mx-4 animate-in zoom-in-95 duration-200">
        {/* Close button */}
        <button
          onClick={onClose}
          aria-label="Close"
          className="absolute -top-2 -right-2 z-10 flex h-8 w-8 items-center justify-center rounded-full bg-card border border-border/50 text-muted-foreground hover:text-white transition-colors"
        >
          <X className="h-4 w-4" />
        </button>

        <div className="rounded-xl border border-border/50 bg-card/95 backdrop-blur-md p-6">
          {/* Header */}
          <div className="text-center mb-6">
            <h2 className="text-xl font-bold text-white">
              Upgrade Your Plan
            </h2>
            <p className="text-sm text-muted-foreground mt-1">
              Unlock powerful trading features with a premium subscription
            </p>
          </div>

          {/* Plan cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {PLANS.map((plan) => {
              const isCurrent = tier === plan.tier;
              const isDowngrade = tierRank[tier] > tierRank[plan.tier];

              return (
                <Card
                  key={plan.tier}
                  className={`bg-card/50 border-border/50 relative overflow-hidden ${
                    plan.highlight
                      ? "ring-1 ring-blue-500/50"
                      : ""
                  }`}
                >
                  {plan.highlight && (
                    <div className="absolute top-0 inset-x-0 h-0.5 bg-gradient-to-r from-blue-500 to-cyan-500" />
                  )}

                  <CardHeader className="pb-2 pt-5 px-5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {plan.icon}
                        <CardTitle className="text-base font-semibold text-white">
                          {plan.name}
                        </CardTitle>
                      </div>
                      {isCurrent && (
                        <Badge className="bg-blue-600/20 text-blue-400 border-blue-500/30 text-[10px]">
                          Current Plan
                        </Badge>
                      )}
                    </div>
                    <div className="mt-3">
                      <span className="text-3xl font-bold text-white">
                        {plan.price}
                      </span>
                      <span className="text-sm text-muted-foreground">
                        {plan.period}
                      </span>
                    </div>
                  </CardHeader>

                  <CardContent className="px-5 pb-5">
                    <ul className="space-y-2 mb-5">
                      {plan.features.map((feature) => (
                        <li
                          key={feature}
                          className="flex items-start gap-2 text-sm text-muted-foreground"
                        >
                          <Check className="h-4 w-4 text-green-400 mt-0.5 shrink-0" />
                          {feature}
                        </li>
                      ))}
                    </ul>

                    <Button
                      className={`w-full gap-2 ${
                        plan.highlight && !isCurrent
                          ? "bg-blue-600 hover:bg-blue-700 text-white"
                          : ""
                      }`}
                      variant={
                        isCurrent || isDowngrade ? "outline" : "default"
                      }
                      disabled={isCurrent || isDowngrade || loading}
                      onClick={() => subscribe(plan.tier)}
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
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Footer note */}
          <p className="text-center text-xs text-muted-foreground mt-4">
            Cancel anytime. Powered by Stripe for secure payments.
          </p>
        </div>
      </div>
    </div>
  );
}
