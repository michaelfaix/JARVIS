// =============================================================================
// src/app/api/stripe/webhook/route.ts — Stripe Webhook Handler
// =============================================================================

import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

// Use service-role or anon key for webhook (no user session available)
function getSupabaseAdmin() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.text();
    const signature = req.headers.get("stripe-signature");

    const secretKey = process.env.STRIPE_SECRET_KEY;
    if (!secretKey || secretKey === "sk_test_placeholder") {
      console.warn("[stripe/webhook] STRIPE_SECRET_KEY not configured, skipping");
      return NextResponse.json({ received: true });
    }

    const Stripe = (await import("stripe")).default;
    const stripe = new Stripe(secretKey, {
      apiVersion: "2026-02-25.clover",
    });

    let event;

    const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;
    if (webhookSecret && webhookSecret !== "whsec_placeholder") {
      if (!signature) {
        return NextResponse.json(
          { error: "Missing stripe-signature header" },
          { status: 400 }
        );
      }
      event = stripe.webhooks.constructEvent(body, signature, webhookSecret);
    } else {
      console.warn(
        "[stripe/webhook] STRIPE_WEBHOOK_SECRET not configured — skipping signature verification"
      );
      event = JSON.parse(body);
    }

    if (event.type === "checkout.session.completed") {
      const session = event.data.object;
      const userId = session.metadata?.user_id;
      const tier = session.metadata?.tier;

      if (userId && tier) {
        const supabase = getSupabaseAdmin();
        const { error } = await supabase
          .from("profiles")
          .update({
            tier,
            stripe_customer_id: session.customer,
            stripe_subscription_id: session.subscription,
          })
          .eq("id", userId);

        if (error) {
          console.error("[stripe/webhook] Failed to update profile:", error);
        } else {
          console.log(
            `[stripe/webhook] Updated user ${userId} to tier: ${tier}`
          );
        }
      }
    }

    if (event.type === "customer.subscription.deleted") {
      const subscription = event.data.object;
      const supabase = getSupabaseAdmin();

      // Downgrade user back to free when subscription is cancelled
      const { error } = await supabase
        .from("profiles")
        .update({ tier: "free", stripe_subscription_id: null })
        .eq("stripe_subscription_id", subscription.id);

      if (error) {
        console.error("[stripe/webhook] Failed to downgrade profile:", error);
      }
    }

    return NextResponse.json({ received: true });
  } catch (error) {
    console.error("[stripe/webhook] Error:", error);
    return NextResponse.json(
      { error: "Webhook handler failed" },
      { status: 500 }
    );
  }
}
