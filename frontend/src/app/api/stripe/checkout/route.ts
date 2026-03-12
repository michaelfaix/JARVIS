// =============================================================================
// src/app/api/stripe/checkout/route.ts — Create Stripe Checkout Session
// =============================================================================

import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

const PRICE_MAP: Record<string, { priceEnvKey: string; fallbackAmount: number }> = {
  pro: { priceEnvKey: "STRIPE_PRO_PRICE_ID", fallbackAmount: 2900 },
  enterprise: { priceEnvKey: "STRIPE_ENTERPRISE_PRICE_ID", fallbackAmount: 19900 },
};

export async function POST(req: NextRequest) {
  try {
    const { tier } = await req.json();

    if (!tier || !PRICE_MAP[tier]) {
      return NextResponse.json(
        { error: "Invalid tier. Must be 'pro' or 'enterprise'." },
        { status: 400 }
      );
    }

    // Check auth
    const supabase = createClient();
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // If Stripe is not configured, return mock URL
    const secretKey = process.env.STRIPE_SECRET_KEY;
    if (!secretKey || secretKey === "sk_test_placeholder") {
      return NextResponse.json({ url: "/settings?upgraded=mock" });
    }

    // Dynamic import to keep stripe out of client bundle
    const Stripe = (await import("stripe")).default;
    const stripe = new Stripe(secretKey, {
      apiVersion: "2026-02-25.clover",
    });

    const priceId = process.env[PRICE_MAP[tier].priceEnvKey];

    const origin = req.headers.get("origin") ?? "http://localhost:3000";

    const sessionParams: Record<string, unknown> = {
      mode: "subscription",
      customer_email: user.email,
      success_url: `${origin}/settings?upgraded=true`,
      cancel_url: `${origin}/settings`,
      metadata: {
        user_id: user.id,
        tier,
      },
    };

    // Use price ID if configured, otherwise create an ad-hoc price
    if (priceId && !priceId.startsWith("price_") === false) {
      sessionParams.line_items = [{ price: priceId, quantity: 1 }];
    } else if (priceId && priceId !== `price_${tier}_placeholder`) {
      sessionParams.line_items = [{ price: priceId, quantity: 1 }];
    } else {
      // Ad-hoc price for development/testing
      sessionParams.line_items = [
        {
          price_data: {
            currency: "eur",
            product_data: {
              name: `JARVIS Trader ${tier.charAt(0).toUpperCase() + tier.slice(1)}`,
              description: `${tier === "pro" ? "Pro" : "Enterprise"} subscription`,
            },
            unit_amount: PRICE_MAP[tier].fallbackAmount,
            recurring: { interval: "month" },
          },
          quantity: 1,
        },
      ];
    }

    const session = await stripe.checkout.sessions.create(
      sessionParams as Parameters<typeof stripe.checkout.sessions.create>[0]
    );

    return NextResponse.json({ url: session.url });
  } catch (error) {
    console.error("[stripe/checkout] Error:", error);
    return NextResponse.json(
      { error: "Failed to create checkout session" },
      { status: 500 }
    );
  }
}
